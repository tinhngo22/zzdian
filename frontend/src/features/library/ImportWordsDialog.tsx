import { useId, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/Button";
import { Dialog } from "../../components/Dialog";
import { TextArea } from "../../components/TextInput";
import { errorMessage } from "./format";
import { useAddWords } from "./hooks";
import {
  COLUMN_LAYOUTS,
  FIELD_LABELS,
  FIELD_SEPARATORS,
  MAX_IMPORT_WORDS,
  parseImport,
  ROW_SEPARATORS,
  type ColumnLayout,
  type ImportField,
  type ParsedRow,
} from "./importWords";

type FieldChoice = keyof typeof FIELD_SEPARATORS | "custom";
type RowChoice = keyof typeof ROW_SEPARATORS | "custom";

const PREVIEW_LIMIT = 100;

const CELL_LANG: Partial<Record<ImportField, string>> = {
  simplified: "zh-Hans",
  traditional: "zh-Hant",
};

export function ImportWordsDialog({ setId, onClose }: { setId: string; onClose: () => void }) {
  const textRef = useRef<HTMLTextAreaElement>(null);
  const [text, setText] = useState("");
  const [fieldChoice, setFieldChoice] = useState<FieldChoice>("tab");
  const [customField, setCustomField] = useState("");
  const [rowChoice, setRowChoice] = useState<RowChoice>("newline");
  const [customRow, setCustomRow] = useState("");
  const [layout, setLayout] = useState<ColumnLayout>("spd");
  const addWords = useAddWords(setId);

  const fieldSeparator = fieldChoice === "custom" ? customField : FIELD_SEPARATORS[fieldChoice];
  const rowSeparator = rowChoice === "custom" ? customRow : ROW_SEPARATORS[rowChoice];
  const rows = useMemo(
    () => parseImport(text, { fieldSeparator, rowSeparator, layout }),
    [text, fieldSeparator, rowSeparator, layout],
  );
  const words = rows.flatMap((r) => (r.word ? [r.word] : []));
  const skipped = rows.length - words.length;
  const tooMany = words.length > MAX_IMPORT_WORDS;
  const missingSeparator = !fieldSeparator || !rowSeparator;
  const fields = COLUMN_LAYOUTS[layout];

  const placeholderSep = fieldChoice === "tab" ? "\t" : fieldSeparator || " | ";
  const placeholder = (
    [
      { simplified: "你好", traditional: "你好", pinyin: "nǐ hǎo", definitions: "hello" },
      { simplified: "谢谢", traditional: "謝謝", pinyin: "xiè xie", definitions: "thank you" },
    ] as const
  )
    .map((w) => fields.map((f) => w[f]).join(placeholderSep))
    .join(rowChoice === "newline" ? "\n" : `${rowSeparator || " | "}\n`);

  const canImport = words.length > 0 && !tooMany && !missingSeparator;
  const importWords = () => {
    if (canImport) addWords.mutate(words, { onSuccess: onClose });
  };

  return (
    <Dialog
      open
      onClose={addWords.isPending ? () => {} : onClose}
      title="Import words"
      description="Paste words from a spreadsheet, Quizlet export, or any list. One word per row."
      size="lg"
      initialFocusRef={textRef}
      footer={
        <>
          {words.length > 0 && (
            <span className="mr-auto text-sm text-stone-500" aria-live="polite">
              {skipped > 0 && `${skipped} ${skipped === 1 ? "row" : "rows"} will be skipped`}
            </span>
          )}
          <Button variant="secondary" onClick={onClose} disabled={addWords.isPending}>
            Cancel
          </Button>
          <Button onClick={importWords} disabled={!canImport} pending={addWords.isPending}>
            {words.length > 0
              ? `Import ${words.length} ${words.length === 1 ? "word" : "words"}`
              : "Import"}
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-5">
        <TextArea
          ref={textRef}
          label="Your words"
          rows={8}
          lang="zh-Hans"
          className="font-cjk"
          spellCheck={false}
          placeholder={placeholder}
          value={text}
          onChange={(e) => setText(e.target.value)}
          hint={`Columns: ${fields.map((f) => FIELD_LABELS[f]).join(", ")}. Only the Chinese word is required.`}
        />

        <div className="grid grid-cols-3 gap-5 max-md:grid-cols-1">
          <SeparatorChoice
            legend="Between columns"
            name="field-separator"
            options={[
              { value: "tab", label: "Tab" },
              { value: "comma", label: "Comma" },
            ]}
            choice={fieldChoice}
            onChoice={(v) => setFieldChoice(v as FieldChoice)}
            custom={customField}
            onCustom={setCustomField}
          />
          <SeparatorChoice
            legend="Between words"
            name="row-separator"
            options={[
              { value: "newline", label: "New line" },
              { value: "semicolon", label: "Semicolon" },
            ]}
            choice={rowChoice}
            onChoice={(v) => setRowChoice(v as RowChoice)}
            custom={customRow}
            onCustom={setCustomRow}
          />
          <LayoutSelect layout={layout} onChange={setLayout} />
        </div>

        <Preview rows={rows} fields={fields} />

        {tooMany && (
          <p role="alert" className="text-sm text-rose-700">
            You can import up to {MAX_IMPORT_WORDS} words at a time ({words.length} found). Split
            the list and import it in parts.
          </p>
        )}
        {addWords.error && (
          <p role="alert" className="text-sm text-rose-700">
            {errorMessage(addWords.error, "This set no longer exists.")}
          </p>
        )}
      </div>
    </Dialog>
  );
}

const RADIO = "size-4 accent-red-700";
const SMALL_INPUT =
  "h-8 w-24 rounded-md border border-stone-300 bg-white px-2 text-sm text-stone-900 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-red-700 disabled:bg-stone-50 disabled:text-stone-400";

function SeparatorChoice({
  legend,
  name,
  options,
  choice,
  onChoice,
  custom,
  onCustom,
}: {
  legend: string;
  name: string;
  options: { value: string; label: string }[];
  choice: string;
  onChoice: (value: string) => void;
  custom: string;
  onCustom: (value: string) => void;
}) {
  const groupName = `${useId()}-${name}`;
  const customSelected = choice === "custom";
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-2 text-sm font-medium text-stone-700">{legend}</legend>
      {options.map((o) => (
        <RadioRow key={o.value}>
          <input
            type="radio"
            name={groupName}
            className={RADIO}
            checked={choice === o.value}
            onChange={() => onChoice(o.value)}
          />
          {o.label}
        </RadioRow>
      ))}
      <div className="flex items-center gap-2">
        <RadioRow>
          <input
            type="radio"
            name={groupName}
            className={RADIO}
            checked={customSelected}
            onChange={() => onChoice("custom")}
          />
          Custom
        </RadioRow>
        <input
          aria-label={`${legend}: custom separator`}
          className={SMALL_INPUT}
          placeholder="e.g. |"
          value={custom}
          disabled={!customSelected}
          onChange={(e) => onCustom(e.target.value)}
        />
      </div>
      {customSelected && !custom && (
        <p className="text-xs text-rose-700">Enter a separator.</p>
      )}
    </fieldset>
  );
}

function RadioRow({ children }: { children: ReactNode }) {
  return <label className="flex items-center gap-2 text-sm text-stone-800">{children}</label>;
}

function LayoutSelect({ layout, onChange }: { layout: ColumnLayout; onChange: (l: ColumnLayout) => void }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="mb-2 text-sm font-medium text-stone-700">
        Column order
      </label>
      <select
        id={id}
        value={layout}
        onChange={(e) => onChange(e.target.value as ColumnLayout)}
        className="h-10 rounded-lg border border-stone-300 bg-white px-2 text-sm text-stone-900 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-red-700"
      >
        {(Object.keys(COLUMN_LAYOUTS) as ColumnLayout[]).map((key) => (
          <option key={key} value={key}>
            {COLUMN_LAYOUTS[key].map((f) => FIELD_LABELS[f]).join(" · ")}
          </option>
        ))}
      </select>
    </div>
  );
}

function Preview({
  rows,
  fields,
}: {
  rows: ParsedRow[];
  fields: readonly ImportField[];
}) {
  if (rows.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-stone-300 px-4 py-6 text-center text-sm text-stone-500">
        A preview of the words appears here as you paste.
      </p>
    );
  }
  const shown = rows.slice(0, PREVIEW_LIMIT);
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-medium text-stone-700">Preview</h3>
      <div className="max-h-72 overflow-auto rounded-xl border border-stone-200">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-stone-50 text-xs font-medium text-stone-500">
            <tr>
              <th scope="col" className="w-12 px-3 py-2">
                #
              </th>
              {fields.map((f) => (
                <th key={f} scope="col" className="px-3 py-2">
                  {FIELD_LABELS[f]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-100">
            {shown.map((r) => (
              <tr key={r.row} className={r.error ? "bg-rose-50" : undefined}>
                <td className="px-3 py-2 text-stone-400 tabular-nums">{r.row}</td>
                {r.word ? (
                  fields.map((f) => (
                    <td
                      key={f}
                      lang={CELL_LANG[f]}
                      className={`px-3 py-2 align-top whitespace-pre-line ${
                        CELL_LANG[f] ? "font-cjk text-base text-stone-900" : "text-stone-700"
                      }`}
                    >
                      {r.word[f] ?? <span className="text-stone-300">—</span>}
                    </td>
                  ))
                ) : (
                  <td colSpan={fields.length} className="px-3 py-2 text-rose-700">
                    {r.error}: <span className="text-rose-900">{r.raw}</span>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > PREVIEW_LIMIT && (
        <p className="text-xs text-stone-500">
          Showing the first {PREVIEW_LIMIT} of {rows.length} rows.
        </p>
      )}
    </div>
  );
}
