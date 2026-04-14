'use client'

import { ResearchMap } from '@/components/map/ResearchMap'
import { PipelineStepper } from '@/components/pipeline/PipelineStepper'
import { NextStepPrompt } from '@/components/pipeline/NextStepPrompt'
import { BottomBar } from '@/components/map/BottomBar'
import { DiscoveryToast } from '@/components/map/DiscoveryToast'
import { DetailDrawer } from '@/components/drawers/DetailDrawer'
import { ReviewDrawer } from '@/components/drawers/ReviewDrawer'
import { DebateDrawer } from '@/components/drawers/DebateDrawer'
import { ExperimentDrawer } from '@/components/drawers/ExperimentDrawer'
import { DashboardDrawer } from '@/components/drawers/DashboardDrawer'
import { FeedbackDrawer } from '@/components/drawers/FeedbackDrawer'

export default function HomePage() {
  return (
    <div className="h-screen w-screen flex flex-col bg-void overflow-hidden">
      {/* Topbar */}
      <PipelineStepper />

      {/* Main content: map fills remaining space */}
      <div className="flex-1 relative min-h-0 min-h-[500px]">
        <ResearchMap />

        {/* Floating UI elements over the map */}
        <NextStepPrompt />
        <DiscoveryToast />
      </div>

      {/* Bottom stats strip */}
      <BottomBar />

      {/* Drawer overlays — rendered on top of everything */}
      <DetailDrawer />
      <ReviewDrawer />
      <DebateDrawer />
      <ExperimentDrawer />
      <DashboardDrawer />
      <FeedbackDrawer />
    </div>
  )
}
