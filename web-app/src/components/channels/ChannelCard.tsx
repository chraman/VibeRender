export default function CreateChannelPage() {
  return (
    <div className="max-w-md">
      <h1 className="text-xl font-semibold mb-4">
        Create / Link Channel
      </h1>

      <input
        placeholder="Channel Name"
        className="border p-2 w-full mb-4"
      />

      <button className="bg-black text-white px-4 py-2 rounded">
        Save
      </button>
    </div>
  );
}
