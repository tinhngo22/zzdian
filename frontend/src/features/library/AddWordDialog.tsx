import { useId, useRef, useState, type FormEvent } from "react";
import { Button } from "../../components/Button";
import { Dialog } from "../../components/Dialog";
import { TextArea, TextInput } from "../../components/TextInput";
import type { DictionaryWord, NewSetWord } from "../../types/api";
import { errorMessage } from "./format";
import { useAddWord, useDictionaryLookup } from "./hooks";

const EMPTY = { simplified: "", traditional: "", pinyin: "", definitions: "" };
const NO_AUTOFILL = { pinyin: "", definitions: "" };

type AutofillField = keyof typeof NO_AUTOFILL;
const AUTOFILL_FIELDS: AutofillField[] = ["pinyin", "definitions"];

type Lookup =
  | { status: "idle" }
  | { status: "pending"; word: string }
  | { status: "done"; word: string; entries: DictionaryWord[]; selectedId: number | null };

export function AddWordDialog({ setId, onClose }: { setId: string; onClose: () => void }) {
  const formId = useId();
  const formRef = useRef<HTMLFormElement>(null);
  const simplifiedRef = useRef<HTMLInputElement>(null);
  const addAnotherRef = useRef(false);
  const [fields, setFields] = useState(EMPTY);
  const [simplifiedError, setSimplifiedError] = useState<string | null>(null);
  const [lastAdded, setLastAdded] = useState<string | null>(null);
  const [lookup, setLookup] = useState<Lookup>({ status: "idle" });
  const addWord = useAddWord(setId);
  const lookupWord = useDictionaryLookup();

  const fieldsRef = useRef(fields);
  fieldsRef.current = fields;
  // What autofill last wrote; a field that still holds it was not edited by the user.
  const autofilledRef = useRef(NO_AUTOFILL);
  const lookedUpWordRef = useRef("");

  const update = (key: keyof typeof EMPTY) => (value: string) => {
    setFields((f) => ({ ...f, [key]: value }));
    if (key === "simplified") setSimplifiedError(null);
  };

  /** Fill pinyin and definitions from `entry` (or clear them when null), sparing user edits unless `force`. */
  const applyEntry = (entry: DictionaryWord | null, force = false) => {
    const values = {
      pinyin: entry?.pinyin ?? "",
      definitions: entry?.definitions.join("\n") ?? "",
    };
    const current = fieldsRef.current;
    const patch: Partial<typeof NO_AUTOFILL> = {};
    for (const key of AUTOFILL_FIELDS) {
      if (force || !current[key].trim() || current[key] === autofilledRef.current[key]) {
        patch[key] = values[key];
      }
    }
    autofilledRef.current = { ...autofilledRef.current, ...patch };
    setFields((f) => ({ ...f, ...patch }));
  };

  const handleSimplifiedBlur = async () => {
    const word = fields.simplified.trim();
    if (word === lookedUpWordRef.current) return;
    lookedUpWordRef.current = word;
    if (!word) {
      setLookup({ status: "idle" });
      applyEntry(null);
      return;
    }

    setLookup({ status: "pending", word });
    let entries: DictionaryWord[];
    try {
      entries = (await lookupWord(word)).entries;
    } catch {
      // Autofill is a convenience: on failure, leave the fields for the user to fill.
      if (lookedUpWordRef.current === word) setLookup({ status: "idle" });
      return;
    }
    if (lookedUpWordRef.current !== word) return;

    const entry = entries[0] ?? null;
    setLookup({ status: "done", word, entries, selectedId: entry?.id ?? null });
    applyEntry(entry);
  };

  const chooseEntry = (entry: DictionaryWord) => {
    setLookup((l) => (l.status === "done" ? { ...l, selectedId: entry.id } : l));
    applyEntry(entry, true);
  };

  const resetAutofill = () => {
    autofilledRef.current = NO_AUTOFILL;
    lookedUpWordRef.current = "";
    setLookup({ status: "idle" });
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const addAnother = addAnotherRef.current;
    addAnotherRef.current = false;

    const simplified = fields.simplified.trim();
    if (!simplified) {
      setSimplifiedError("Enter the word in simplified Chinese.");
      simplifiedRef.current?.focus();
      return;
    }
    // Optional fields are omitted when empty; definitions stays one free-form string.
    const body: NewSetWord = { simplified };
    const traditional = fields.traditional.trim();
    const pinyin = fields.pinyin.trim();
    const definitions = fields.definitions.trim();
    if (traditional) body.traditional = traditional;
    if (pinyin) body.pinyin = pinyin;
    if (definitions) body.definitions = definitions;

    addWord.mutate(body, {
      onSuccess: (word) => {
        if (!addAnother) {
          onClose();
          return;
        }
        setFields(EMPTY);
        resetAutofill();
        setLastAdded(word.simplified);
        addWord.reset();
        simplifiedRef.current?.focus();
      },
    });
  };

  const lookupHint =
    lookup.status === "pending" && lookup.word === fields.simplified.trim()
      ? "Looking up pinyin and definitions…"
      : lookup.status === "done" && lookup.word === fields.simplified.trim()
        ? lookup.entries.length
          ? "Pinyin and definitions filled in from the dictionary. You can edit them."
          : "Not in the dictionary. Fill in pinyin and definitions yourself."
        : undefined;
  const readings =
    lookup.status === "done" && lookup.word === fields.simplified.trim() && lookup.entries.length > 1
      ? lookup
      : null;

  return (
    <Dialog
      open
      onClose={addWord.isPending ? () => {} : onClose}
      title="Add word"
      initialFocusRef={simplifiedRef}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={addWord.isPending}>
            Cancel
          </Button>
          <Button
            variant="secondary"
            disabled={addWord.isPending}
            onClick={() => {
              addAnotherRef.current = true;
              formRef.current?.requestSubmit();
            }}
          >
            Add another
          </Button>
          <Button type="submit" form={formId} pending={addWord.isPending}>
            Add word
          </Button>
        </>
      }
    >
      <form
        ref={formRef}
        id={formId}
        noValidate
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
      >
        {lastAdded && (
          <p role="status" className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            Added <span lang="zh-Hans" className="font-cjk">{lastAdded}</span>. Add another word below.
          </p>
        )}
        <div className="flex flex-col gap-2">
          <TextInput
            ref={simplifiedRef}
            label="Chinese word (simplified)"
            lang="zh-Hans"
            className="font-cjk text-lg"
            value={fields.simplified}
            onChange={(e) => update("simplified")(e.target.value)}
            onBlur={() => void handleSimplifiedBlur()}
            error={simplifiedError}
            hint={lookupHint}
            required
          />
          {readings && (
            <div role="group" aria-label="Dictionary readings" className="flex flex-wrap gap-2">
              {readings.entries.map((entry) => (
                <Button
                  key={entry.id}
                  size="sm"
                  variant={entry.id === readings.selectedId ? "primary" : "secondary"}
                  aria-pressed={entry.id === readings.selectedId}
                  title={entry.definitions.join("; ")}
                  onClick={() => chooseEntry(entry)}
                >
                  {entry.pinyin}
                </Button>
              ))}
            </div>
          )}
        </div>
        <div className="grid grid-cols-2 gap-4 max-md:grid-cols-1">
          <TextInput
            label="Traditional"
            optional
            lang="zh-Hant"
            className="font-cjk"
            value={fields.traditional}
            onChange={(e) => update("traditional")(e.target.value)}
          />
          <TextInput
            label="Pinyin"
            optional
            placeholder="nǐ hǎo"
            value={fields.pinyin}
            onChange={(e) => update("pinyin")(e.target.value)}
          />
        </div>
        <TextArea
          label="Definitions"
          optional
          rows={4}
          placeholder={"hello\nhi"}
          value={fields.definitions}
          onChange={(e) => update("definitions")(e.target.value)}
          hint="Free text. Line breaks are kept."
        />
        {addWord.error && (
          <p role="alert" className="text-sm text-rose-700">
            {errorMessage(addWord.error, "This set no longer exists.")}
          </p>
        )}
      </form>
    </Dialog>
  );
}
