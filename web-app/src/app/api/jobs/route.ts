import { NextRequest, NextResponse } from "next/server";
import { createJob } from "@/lib/db/queries/jobs";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const job = await createJob({
    channelId: body.channelId,
    topic: body.topic,
    videoTheme: body.videoTheme,
    emotionalGoal: body.emotionalGoal,
    pacing: body.pacing,
  });

  return NextResponse.json(job, { status: 201 });
}
