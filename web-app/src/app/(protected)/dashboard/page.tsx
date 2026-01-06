import Dashboard from "@/components/channels/Dashboard";
import { getUserChannels } from "@/lib/db/queries/channels";

export default async function Page() {
  const channels = await getUserChannels("3f29239d-5a72-472c-bc31-7c9af1d606ce");;
  return <Dashboard channels={channels} />;
}
