import { Button } from "../../components/Button";
import { InlineSpinner } from "../../components/States";
import type { CharacterComponent } from "../../types/api";
import { BigGlyph, FactList, joinReadings } from "./CharacterFacts";
import { useWordCharacters } from "./hooks";
import { RelatedWords } from "./RelatedWords";

const ROLE_LABELS: Record<string, string> = {
  semantic: "Semantic (hints at meaning)",
  phonetic: "Phonetic (hints at sound)",
};

interface ComponentPanelProps {
  component: CharacterComponent;
  /** The word the modal is showing; it is left out of the related words. */
  currentSimplified: string;
}

/**
 * The component row from the character breakdown is shown right away; stroke count and
 * the component's own parts are looked up separately (strokes like ㇀ have no entry).
 */
export function ComponentPanel({ component, currentSimplified }: ComponentPanelProps) {
  const details = useWordCharacters(component.glyph);
  const character = details.data?.characters[0]?.character ?? null;
  const parts = character?.components.length ? (
    <span lang="zh-Hans" className="font-cjk">
      {character.components.map((c) => c.glyph).join(" + ")}
    </span>
  ) : null;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start gap-4">
        <BigGlyph glyph={component.glyph} size="md" />
        <FactList
          compact
          facts={[
            { label: "Role", value: ROLE_LABELS[component.role] ?? null },
            { label: "Pinyin", value: joinReadings(character?.pinyin ?? component.pinyin) },
            {
              label: "Meaning",
              value: (character?.meaning_en ?? component.meaning_en)?.trim() || null,
            },
            { label: "Strokes", value: character?.stroke_count?.toString() ?? null },
            { label: "Parts", value: parts },
          ]}
        />
      </div>
      {details.isPending && <InlineSpinner label="Loading details" />}
      {details.isError && (
        <div role="alert" className="flex items-center gap-2 text-sm text-rose-700">
          Couldn't load details.
          <Button size="sm" variant="ghost" onClick={() => details.refetch()}>
            Retry
          </Button>
        </div>
      )}
      <RelatedWords
        by="component"
        id={component.id}
        glyph={component.glyph}
        currentSimplified={currentSimplified}
      />
    </div>
  );
}
