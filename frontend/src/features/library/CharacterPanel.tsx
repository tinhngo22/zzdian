import type { CharacterComponent, WordCharacterEntry } from "../../types/api";
import { BigGlyph, FactList, joinReadings } from "./CharacterFacts";
import { kangxiRadicalGlyph } from "./format";
import { RelatedWords } from "./RelatedWords";

interface CharacterPanelProps {
  entry: WordCharacterEntry;
  currentSimplified: string;
  /** `position` of the component open in the side panel, if any. */
  selectedComponentPosition: number | null;
  onSelectComponent: (component: CharacterComponent) => void;
}

export function CharacterPanel({
  entry,
  currentSimplified,
  selectedComponentPosition,
  onSelectComponent,
}: CharacterPanelProps) {
  const { glyph, character } = entry;

  if (!character) {
    return (
      <div className="flex items-center gap-6">
        <BigGlyph glyph={glyph} />
        <p className="text-sm text-stone-500">No dictionary data available.</p>
      </div>
    );
  }

  const radicalGlyph =
    character.main_radical_id != null ? kangxiRadicalGlyph(character.main_radical_id) : null;
  const radical = radicalGlyph && (
    <span className="flex items-baseline gap-2">
      <span lang="zh-Hans" className="font-cjk text-lg">
        {radicalGlyph}
      </span>
    </span>
  );
  const components = character.components.length > 0 && (
    <span className="flex flex-wrap items-center gap-1">
      {character.components.map((c, i) => (
        <span key={c.position} className="flex items-center gap-1">
          {i > 0 && (
            <span aria-hidden="true" className="text-stone-400">
              +
            </span>
          )}
          <ComponentButton
            component={c}
            selected={c.position === selectedComponentPosition}
            onClick={() => onSelectComponent(c)}
          />
        </span>
      ))}
    </span>
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start gap-8 max-md:flex-col max-md:gap-4">
        <BigGlyph glyph={character.glyph} />
        <FactList
          facts={[
            { label: "Pinyin", value: joinReadings(character.pinyin) },
            { label: "Meaning", value: character.meaning_en?.trim() || null },
            { label: "Strokes", value: character.stroke_count?.toString() ?? null },
            { label: "Radical", value: radical },
            { label: "Components", value: components },
          ]}
        />
      </div>
      <RelatedWords
        by="character"
        id={character.id}
        glyph={character.glyph}
        currentSimplified={currentSimplified}
      />
    </div>
  );
}

function ComponentButton({
  component,
  selected,
  onClick,
}: {
  component: CharacterComponent;
  selected: boolean;
  onClick: () => void;
}) {
  const meaning = component.meaning_en?.trim();
  return (
    <button
      type="button"
      aria-pressed={selected}
      aria-label={`Component ${component.glyph}${meaning ? `, ${meaning}` : ""}`}
      title={meaning || undefined}
      onClick={onClick}
      className={`rounded-lg border px-2 py-0.5 font-cjk text-lg focus-visible:outline-2 focus-visible:outline-red-700 ${
        selected
          ? "border-red-700 bg-red-50 text-red-800"
          : "border-stone-200 text-stone-900 hover:border-stone-300 hover:bg-stone-50"
      }`}
    >
      <span lang="zh-Hans">{component.glyph}</span>
    </button>
  );
}
