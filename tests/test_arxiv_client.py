import pytest
from unittest.mock import patch, MagicMock
from app.ingestion.arxiv_client import fetch_papers
from app.core.atoms import ResearchAtom

@pytest.mark.asyncio
async def test_fetch_papers_normalization():
    with patch("arxiv.Client") as MockClient:
        mock_client_instance = MockClient.return_value
        
        # Create a mock result matching arxiv.Result
        mock_result = MagicMock()
        mock_result.get_short_id.return_value = "2301.00001v2"
        mock_result.title = "Test Paper"
        mock_result.summary = "Test Abstract"
        
        mock_author = MagicMock()
        mock_author.name = "Test Author"
        mock_result.authors = [mock_author]
        
        mock_result.published.year = 2023
        mock_result.pdf_url = "http://arxiv.org/pdf/2301.00001v2"
        
        mock_client_instance.results.return_value = [mock_result]
        
        # Call the client
        atoms = await fetch_papers("test query", 1)
        
        assert len(atoms) == 1
        atom = atoms[0]
        
        # Assert type and fields
        assert isinstance(atom, ResearchAtom)
        assert atom.paper_id == "2301.00001"
        assert atom.title == "Test Paper"
        assert atom.abstract == "Test Abstract"
        assert atom.authors == [{"name": "Test Author"}]
        assert atom.published_year == 2023
        assert atom.pdf_url == "http://arxiv.org/pdf/2301.00001v2"
        assert atom.methods == []
        assert atom.limitations == []
        assert atom.claims == []
        assert atom.embedding is None
        assert atom.arxiv_status == "raw"
