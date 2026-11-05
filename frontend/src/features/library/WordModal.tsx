import { useState } from "react";
import { Button } from "../../components/Button";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { Dialog } from "../../components/Dialog";
import { InlineSpinner } from "../../components/States";
import { Tabs, type TabItem } from "../../components/Tabs";
import type { CharacterComponent, SetWord } from "../../types/api";
import { CharacterPanel } from "./CharacterPanel";
import { ComponentPanel } from "./ComponentPanel";
import { errorMessage } from "./format";
import {
  EXPLORE_MAX_CHARACTERS,
  useRemoveWord,
  useWordCharacters,
  wordCharacterIds,
} from "./hooks";
import { WordInfoPanel } from "./WordInfoPanel";

const INFO_TAB = "info";

interface WordModalProps {
  setId: string;
  word: SetWord;
  onClose: () => void;
}

export function WordModal({ setId, word, onClose }: WordModalProps) {
  const [tab, setTab] = useState(INFO_TAB);
  const [component, setComponent] = useState<CharacterComponent | null>(null);
  const [confirmingRemove, setConfirmingRemove] = useState(false);
  const charactersQuery = useWordCharacters(word.simplified);
  const removeWord = useRemoveWord(setId);

  // Repeated glyphs are already collapsed by the backend; skip punctuation, Latin, etc.
  const entries = charactersQuery.data?.characters.filter((c) => c.is_hanzi) ?? [];
  const tabs: TabItem[] = [
    { id: INFO_TAB, label: "Word Info" },
    ...entries.map((entry) => ({
      id: `char-${entry.glyph}`,
      label: <span lang="zh-Hans">{entry.glyph}</span>,
      ariaLabel: `Character ${entry.glyph}`,
      labelClassName: "font-cjk text-base",
    })),
  ];
  const activeEntry = entries.find((e) => `char-${e.glyph}` === tab);
  const selectedTab = tab === INFO_TAB || activeEntry ? tab : INFO_TAB;
  const activeComponent = activeEntry ? component : null;
  const selectTab = (id: string) => {
    setTab(id);
    setComponent(null);
  };
  const tooLong = wordCharacterIds(word.simplified).length > EXPLORE_MAX_CHARACTERS;

  const charactersStatus = tooLong ? (
    <span className="text-xs text-stone-500">Too long to look up characters</span>
  ) : charactersQuery.isPending ? (
    <InlineSpinner label="Loading characters" />
  ) : charactersQuery.isError ? (
    <span role="alert" className="flex items-center gap-2 text-xs text-rose-700">
      Couldn't load characters.
      <Button size="sm" variant="ghost" onClick={() => charactersQuery.refetch()}>
        Retry
      </Button>
    </span>
  ) : null;

  return (
    <>
      <Dialog
        open
        onClose={onClose}
        size="lg"
        title={
          <span className="flex items-baseline gap-3">
            <span lang="zh-Hans" className="font-cjk text-3xl">
              {word.simplified}
            </span>
            {word.pinyin && <span className="text-base font-normal text-stone-500">{word.pinyin}</span>}
          </span>
        }
        footer={
          <>
            <Button
              variant="dangerGhost"
              className="mr-auto"
              onClick={() => setConfirmingRemove(true)}
            >
              Remove from set
            </Button>
            <Button variant="secondary" onClick={onClose}>
              Close
            </Button>
          </>
        }
        aside={
          activeComponent
            ? {
                title: (
                  <span className="flex items-baseline gap-2">
                    Component
                    <span lang="zh-Hans" className="font-cjk text-2xl">
                      {activeComponent.glyph}
                    </span>
                  </span>
                ),
                closeLabel: "Close component",
                onClose: () => setComponent(null),
                children: (
                  <ComponentPanel
                    key={activeComponent.position}
                    component={activeComponent}
                    currentSimplified={word.simplified}
                  />
                ),
              }
            : undefined
        }
      >
        <Tabs
          items={tabs}
          selectedId={selectedTab}
          onSelect={selectTab}
          label="Word details"
          trailing={charactersStatus && <div className="ml-auto pl-2">{charactersStatus}</div>}
        >
          {activeEntry ? (
            <CharacterPanel
              key={activeEntry.glyph}
              entry={activeEntry}
              currentSimplified={word.simplified}
              selectedComponentPosition={activeComponent?.position ?? null}
              onSelectComponent={setComponent}
            />
          ) : (
            <WordInfoPanel word={word} />
          )}
        </Tabs>
      </Dialog>

      <ConfirmDialog
        open={confirmingRemove}
        title="Remove word?"
        message={
          <p>
            Remove <span lang="zh-Hans" className="font-cjk font-semibold">{word.simplified}</span>{" "}
            from this set? This cannot be undone.
          </p>
        }
        confirmLabel="Remove"
        pending={removeWord.isPending}
        error={removeWord.error ? errorMessage(removeWord.error, "This word is no longer in the set.") : null}
        onConfirm={() =>
          removeWord.mutate(word.id, {
            onSuccess: () => {
              setConfirmingRemove(false);
              onClose();
            },
          })
        }
        onCancel={() => {
          setConfirmingRemove(false);
          removeWord.reset();
        }}
      />
    </>
  );
}
