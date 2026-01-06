// src/app/api/channels/route.ts
import { NextRequest, NextResponse } from "next/server";
import { createChannel, getUserChannels } from "@/lib/db/queries/channels";

export async function POST(req: NextRequest) {
  const json = await req.json();
  const newChannel = await createChannel(json);
  return NextResponse.json(newChannel);
}

export async function GET() {
  const channels = await getUserChannels("3f29239d-5a72-472c-bc31-7c9af1d606ce");
  return NextResponse.json(channels);
}
