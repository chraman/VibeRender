import "dotenv/config";
import dotenv from "dotenv";
dotenv.config({ path: ".env.local" });

import { db } from "./index";
import { users, channels, jobs } from "./schema";
async function seed() {
  console.log("🌱 Seeding database...");

  // 1️⃣ Create user
  const [user] = await db
    .insert(users)
    .values({
      email: "demo@viberender.ai",
      name: "Demo User",
    })
    .returning();

  console.log("✅ User created:", user.id);

  // 2️⃣ Create channel
  const [channel] = await db
    .insert(channels)
    .values({
      userId: user.id, // UUID string
      name: "Demo YouTube Channel",
      platform: "youtube",
    })
    .returning();

  console.log("✅ Channel created:", channel.id);

  // 3️⃣ Create jobs
  await db.insert(jobs).values([
    {
      channelId: channel.id,
      topic: "AI horror story",
      status: "pending",
    },
    {
      channelId: channel.id,
      topic: "Motivational short",
      status: "processing",
    },
  ]);

  console.log("✅ Jobs created");

  console.log("🎉 Seeding complete");
  process.exit(0);
}

seed().catch((err) => {
  console.error("❌ Seeding failed:", err);
  process.exit(1);
});
