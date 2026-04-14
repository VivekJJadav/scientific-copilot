"""PaperClusterer: HDBSCAN clustering on paper embeddings with TF-IDF labels."""

import numpy as np
import structlog
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config.settings import settings
from app.db.models import Paper, PaperCluster

logger = structlog.get_logger(__name__)


class PaperClusterer:
    """Clusters papers using HDBSCAN on their embeddings."""

    async def run(self, db: AsyncSession) -> dict:
        """Fetch papers with embeddings, cluster them, persist results.

        Returns:
            {clusters_created: int, papers_clustered: int}
        """
        stmt = select(Paper).where(Paper.embedding.isnot(None))
        papers = (await db.execute(stmt)).scalars().all()

        if len(papers) < 5:
            logger.warning(
                "clustering_insufficient_papers",
                paper_count=len(papers),
                minimum=5,
                message="Falling back to single cluster for all papers",
            )
            if not papers:
                return {"clusters_created": 0, "papers_clustered": 0}
            # Fallback: create a single cluster containing all papers
            return await self._create_single_cluster(papers, db)

        embeddings = [[float(x) for x in p.embedding] for p in papers]
        labels = self._cluster_embeddings(embeddings)

        # Group papers by cluster label (exclude noise: label == -1)
        clusters: dict[int, list[Paper]] = {}
        noise_count = 0
        for paper, label in zip(papers, labels):
            if label == -1:
                noise_count += 1
                continue
            clusters.setdefault(label, []).append(paper)

        if not clusters:
            logger.warning(
                "clustering_all_noise",
                paper_count=len(papers),
                message="HDBSCAN classified everything as noise, falling back to KMeans",
            )
            from sklearn.cluster import KMeans
            # Try to divide into roughly 5 papers per cluster, max out at 5 clusters
            n_clusters = min(max(2, len(papers) // 5), 5)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            kmeans_labels = kmeans.fit_predict(embeddings)
            
            for paper, label in zip(papers, kmeans_labels):
                clusters.setdefault(int(label), []).append(paper)


        logger.info(
            "clustering_results",
            total_papers=len(papers),
            clusters_found=len(clusters),
            noise_points=noise_count,
        )

        papers_clustered = 0
        for cluster_label, cluster_papers in clusters.items():
            abstracts = [p.abstract for p in cluster_papers]
            label_str = self._generate_cluster_label(abstracts)
            paper_ids = [p.arxiv_id for p in cluster_papers]

            # Compute centroid embedding
            cluster_embeddings = np.array([[float(x) for x in p.embedding] for p in cluster_papers])
            centroid = cluster_embeddings.mean(axis=0).tolist()

            pc = PaperCluster(
                label=label_str,
                top_terms=label_str.split(" · "),
                paper_ids=paper_ids,
                centroid_embedding=centroid,
            )
            db.add(pc)
            await db.flush()  # Get the ID

            for p in cluster_papers:
                p.cluster_id = pc.id
                papers_clustered += 1

        await db.commit()

        return {"clusters_created": len(clusters), "papers_clustered": papers_clustered}

    async def _create_single_cluster(self, papers: list[Paper], db: AsyncSession) -> dict:
        """Fallback: create a single cluster with all papers when HDBSCAN fails."""
        abstracts = [p.abstract for p in papers]
        label_str = self._generate_cluster_label(abstracts)
        paper_ids = [p.arxiv_id for p in papers]

        # Convert pgvector embeddings safely
        valid_embeddings = []
        for p in papers:
            if p.embedding is not None:
                try:
                    valid_embeddings.append([float(x) for x in p.embedding])
                except (TypeError, ValueError):
                    continue

        centroid = None
        if valid_embeddings:
            centroid = np.array(valid_embeddings).mean(axis=0).tolist()

        pc = PaperCluster(
            label=label_str,
            top_terms=label_str.split(" · "),
            paper_ids=paper_ids,
            centroid_embedding=centroid,
        )
        db.add(pc)
        await db.flush()

        for p in papers:
            p.cluster_id = pc.id

        await db.commit()
        return {"clusters_created": 1, "papers_clustered": len(papers)}

    def _cluster_embeddings(self, embeddings: list[list[float]]) -> list[int]:
        """Run HDBSCAN on paper embeddings.

        Returns:
            List of integer cluster labels (-1 = noise).
        """
        X = np.array(embeddings)
        clusterer = HDBSCAN(
            min_cluster_size=settings.HDBSCAN_MIN_CLUSTER_SIZE,
            min_samples=settings.HDBSCAN_MIN_SAMPLES,
            metric="euclidean",
        )
        labels = clusterer.fit_predict(X)
        return labels.tolist()

    def _generate_cluster_label(self, abstracts: list[str]) -> str:
        """Generate a human-readable label from cluster abstracts using TF-IDF.

        Returns:
            Top 3 terms joined with ' · ' (e.g. 'transformer · reinforcement · sparse').
        """
        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words="english",
                max_df=0.95,
                min_df=1,
            )
            tfidf_matrix = vectorizer.fit_transform(abstracts)
            feature_names = vectorizer.get_feature_names_out()

            # Sum TF-IDF scores across documents, take top 3
            scores = tfidf_matrix.sum(axis=0).A1
            top_indices = scores.argsort()[-3:][::-1]
            top_terms = [feature_names[i] for i in top_indices]

            return " · ".join(top_terms)
        except Exception as e:
            logger.warning("cluster_label_generation_failed", error=str(e))
            return "unlabeled"
