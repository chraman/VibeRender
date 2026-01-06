"use client";

import { useState } from "react";

export type ChannelDraft = {
  name: string;
  category: string;
  subNiche: string;
  targetAudience: string;
  contentFormat: string;
  brandVoice: string;
  forbiddenTopics: string[];
};

interface Props {
  onCreate: (data: ChannelDraft) => void;
}

export function CreateChannelModal({ onCreate }: Props) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);

  const [draft, setDraft] = useState<ChannelDraft>({
    name: "",
    category: "Story & Entertainment",
    subNiche: "Horror Stories",
    targetAudience: "",
    contentFormat: "",
    brandVoice: "",
    forbiddenTopics: [],
  });

  const canProceed =
    draft.name.trim() &&
    draft.category &&
    draft.subNiche &&
    draft.targetAudience.trim() &&
    draft.contentFormat.trim();

  const close = () => {
    setOpen(false);
    setStep(1);
  };

  return (
    <>
      {/* Trigger */}
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        <span className="text-lg">＋</span>
        Create Channel
      </button>

      {/* Modal */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-white shadow-xl">
            {/* Header */}
            <div className="relative border-b px-5 py-3">
                <h2 className="text-base font-semibold text-slate-900">
                    Create Channel
                </h2>
                <p className="text-xs text-slate-500">
                    Step {step} of 2
                </p>

                {/* Close button */}
                <button
                    onClick={close}
                    aria-label="Close"
                    className="absolute right-3 top-3 rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                    ✕
                </button>
                </div>


            {/* Body */}
            <div className="px-6 py-5">
              {step === 1 && (
                <StepInput draft={draft} setDraft={setDraft} />
              )}

              {step === 2 && <StepReview draft={draft} />}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between border-t px-6 py-4">
              <button
                onClick={step === 1 ? close : () => setStep(1)}
                className="text-sm text-slate-600 hover:text-slate-900"
              >
                Back
              </button>

              {step === 1 && (
                <button
                  disabled={!canProceed}
                  onClick={() => setStep(2)}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                >
                  Review
                </button>
              )}

              {step === 2 && (
                <button
                  onClick={() => {
                    onCreate(draft);
                    close();
                  }}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Create Channel
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
const CATEGORY_OPTIONS = {
  "Story & Entertainment": [
    "Horror Stories",
    "Mystery Stories",
    "Sci-Fi Stories",
    "Mythology",
  ],
  "Education": [
    "History",
    "Psychology",
    "Science Facts",
    "Finance Basics",
  ],
  "Motivation": [
    "Life Advice",
    "Success Stories",
    "Stoicism",
  ],
} as const;

type Category = keyof typeof CATEGORY_OPTIONS;

function StepInput({
  draft,
  setDraft,
}: {
  draft: ChannelDraft;
  setDraft: (d: ChannelDraft) => void;
}) {
  const subNiches = CATEGORY_OPTIONS[draft.category as Category] ?? [];

  return (
    <div className="space-y-4">
      {/* Channel Name */}
      <input
        placeholder="Channel name"
        value={draft.name}
        onChange={(e) => setDraft({ ...draft, name: e.target.value })}
        className="w-full rounded-lg border px-3 py-2 text-sm"
      />

      {/* Category */}
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-600">
          Category
        </label>
        <select
          value={draft.category}
          onChange={(e) =>
            setDraft({
              ...draft,
              category: e.target.value,
              subNiche: "", // reset sub-niche
            })
          }
          className="w-full rounded-lg border px-3 py-2 text-sm bg-white"
        >
          {Object.keys(CATEGORY_OPTIONS).map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      {/* Sub-niche */}
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-600">
          Sub-niche
        </label>
        <select
          value={draft.subNiche}
          onChange={(e) =>
            setDraft({ ...draft, subNiche: e.target.value })
          }
          className="w-full rounded-lg border px-3 py-2 text-sm bg-white"
        >
          <option value="">Select sub-niche</option>
          {subNiches.map((niche) => (
            <option key={niche} value={niche}>
              {niche}
            </option>
          ))}
        </select>
      </div>

      {/* Target Audience */}
      <input
        placeholder="Target audience (e.g. Gen Z, Professionals)"
        value={draft.targetAudience}
        onChange={(e) =>
          setDraft({ ...draft, targetAudience: e.target.value })
        }
        className="w-full rounded-lg border px-3 py-2 text-sm"
      />

      {/* Content Format */}
      <input
        placeholder="Content format (e.g. Short-form AI narration)"
        value={draft.contentFormat}
        onChange={(e) =>
          setDraft({ ...draft, contentFormat: e.target.value })
        }
        className="w-full rounded-lg border px-3 py-2 text-sm"
      />

      {/* Brand Voice */}
      <textarea
        placeholder="Brand voice (tone & style)"
        value={draft.brandVoice}
        onChange={(e) =>
          setDraft({ ...draft, brandVoice: e.target.value })
        }
        className="w-full rounded-lg border px-3 py-2 text-sm"
        rows={3}
      />
    </div>
  );
}


function StepReview({ draft }: { draft: ChannelDraft }) {
  return (
    <div className="space-y-3 text-sm">
      <ReviewRow label="Channel Name" value={draft.name} />
      <ReviewRow label="Category" value={draft.category} />
      <ReviewRow label="Sub-Niche" value={draft.subNiche} />
      <ReviewRow label="Audience" value={draft.targetAudience} />
      <ReviewRow label="Format" value={draft.contentFormat} />
      <ReviewRow label="Brand Voice" value={draft.brandVoice} />
    </div>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-900 text-right">{value}</span>
    </div>
  );
}


