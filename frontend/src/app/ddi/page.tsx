"use client";

import { useState } from "react";
import {
  FaSearch,
  FaTimes,
  FaPlus,
  FaPills,
  FaBook,
  FaChevronRight,
} from "react-icons/fa";

const medicationSuggestions = [
  "Warfarin",
  "Aspirin",
  "Omeprazole",
  "Clopidogrel",
  "Metformin",
  "Atorvastatin",
  "Amlodipine",
  "Simvastatin",
];

interface Interaction {
  drug1: string;
  drug2: string;
  severity: "MAJOR" | "MODERATE" | "MINOR";
  summary: string;
  interpretation: string;
  significance: string;
  evidenceCount: number;
}

const mockInteractions: Interaction[] = [
  {
    drug1: "WARFARIN",
    drug2: "ASPIRIN",
    severity: "MAJOR",
    summary: "Increased risk of bleeding",
    interpretation:
      "Aspirin inhibits platelet aggregation while warfarin affects vitamin K-dependent coagulation factors. The combined effects can increase the anticoagulant and antiplatelet effects.",
    significance:
      "The combination may increase the risk of bleeding, including potentially serious bleeding events.",
    evidenceCount: 3,
  },
  {
    drug1: "WARFARIN",
    drug2: "OMEPRAZOLE",
    severity: "MODERATE",
    summary: "Potential alteration of anticoagulant effect",
    interpretation:
      "Omeprazole may affect the metabolism of warfarin and potentially alter its anticoagulant activity.",
    significance:
      "The interaction may require clinical attention and monitoring of the patient's anticoagulant response.",
    evidenceCount: 2,
  },
];

export default function DDIPage() {
  const [search, setSearch] = useState("");

  const [selectedMedications, setSelectedMedications] =
    useState<string[]>([]);

  const [hasAnalyzed, setHasAnalyzed] = useState(false);

  const filteredMedications = medicationSuggestions.filter(
    (medication) =>
      medication
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      !selectedMedications.includes(medication)
  );

  const addMedication = (medication: string) => {
    if (!selectedMedications.includes(medication)) {
      setSelectedMedications([
        ...selectedMedications,
        medication,
      ]);
    }

    setSearch("");
  };

  const removeMedication = (medication: string) => {
    setSelectedMedications(
      selectedMedications.filter(
        (item) => item !== medication
      )
    );

    setHasAnalyzed(false);
  };

  const handleAnalyze = () => {
    if (selectedMedications.length < 2) {
      return;
    }

    setHasAnalyzed(true);
  };

  const handleAddMedication = () => {
    document
      .getElementById("medication-search")
      ?.focus();
  };

  const getSeverityClass = (
    severity: Interaction["severity"]
  ) => {
    if (severity === "MAJOR") {
      return "bg-red-50 text-red-700 border-red-100";
    }

    if (severity === "MODERATE") {
      return "bg-amber-50 text-amber-700 border-amber-100";
    }

    return "bg-blue-50 text-blue-700 border-blue-100";
  };

  const majorCount = mockInteractions.filter(
    (item) => item.severity === "MAJOR"
  ).length;

  const moderateCount = mockInteractions.filter(
    (item) => item.severity === "MODERATE"
  ).length;

  return (
    <main className="min-h-screen bg-slate-50 px-6 pb-12 pt-24 md:px-8">
      <div className="mx-auto max-w-6xl">

        {/* =====================================================
            PAGE HEADER
        ====================================================== */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <div
              className="
                flex
                h-11
                w-11
                shrink-0
                items-center
                justify-center
                rounded-xl
                bg-blue-50
                text-blue-600
              "
            >
              <FaPills size={19} />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-slate-800">
                Drug–Drug Interaction Checker
              </h1>

              <p className="mt-1 text-sm text-slate-500">
                Select medications to analyze
              </p>
            </div>
          </div>
        </div>

        {/* =====================================================
            SEARCH MEDICATION
        ====================================================== */}
        <section className="mb-7">
          <label
            htmlFor="medication-search"
            className="
              mb-2
              block
              text-sm
              font-semibold
              text-slate-700
            "
          >
            Search medication
          </label>

          <div className="relative">
            <FaSearch
              size={15}
              className="
                pointer-events-none
                absolute
                left-4
                top-1/2
                -translate-y-1/2
                text-slate-400
              "
            />

            <input
              id="medication-search"
              type="text"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Type generic or brand name"
              className="
                h-14
                w-full
                rounded-xl
                border
                border-slate-200
                bg-white
                pl-11
                pr-4
                text-sm
                text-slate-700
                shadow-sm
                outline-none
                transition
                placeholder:text-slate-400
                focus:border-blue-400
                focus:ring-4
                focus:ring-blue-100
              "
            />
          </div>

          {/* SEARCH DROPDOWN */}
          {search.trim() && (
            <div
              className="
                mt-2
                overflow-hidden
                rounded-xl
                border
                border-slate-200
                bg-white
                shadow-lg
              "
            >
              {filteredMedications.length > 0 ? (
                filteredMedications.map((medication) => (
                  <button
                    key={medication}
                    type="button"
                    onClick={() =>
                      addMedication(medication)
                    }
                    className="
                      flex
                      w-full
                      items-center
                      gap-3
                      px-4
                      py-3
                      text-left
                      text-sm
                      text-slate-700
                      transition
                      hover:bg-blue-50
                      hover:text-blue-700
                    "
                  >
                    <FaPills
                      size={14}
                      className="text-blue-500"
                    />

                    <span>{medication}</span>

                    <FaPlus
                      size={11}
                      className="ml-auto text-slate-400"
                    />
                  </button>
                ))
              ) : (
                <div className="px-4 py-4 text-sm text-slate-500">
                  No medication found.
                </div>
              )}
            </div>
          )}
        </section>

        {/* =====================================================
            SELECTED MEDICATIONS
        ====================================================== */}
        <section className="mb-6">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Selected medications
          </h2>

          {selectedMedications.length > 0 ? (
            <div className="flex flex-wrap gap-3">
              {selectedMedications.map((medication) => (
                <div
                  key={medication}
                  className="
                    flex
                    items-center
                    gap-3
                    rounded-xl
                    border
                    border-blue-100
                    bg-white
                    px-4
                    py-2.5
                    shadow-sm
                  "
                >
                  <div
                    className="
                      flex
                      h-8
                      w-8
                      items-center
                      justify-center
                      rounded-lg
                      bg-blue-50
                      text-blue-600
                    "
                  >
                    <FaPills size={13} />
                  </div>

                  <span className="text-sm font-medium text-slate-700">
                    {medication}
                  </span>

                  <button
                    type="button"
                    onClick={() =>
                      removeMedication(medication)
                    }
                    className="
                      flex
                      h-7
                      w-7
                      items-center
                      justify-center
                      rounded-lg
                      text-slate-400
                      transition
                      hover:bg-red-50
                      hover:text-red-500
                    "
                    title={`Remove ${medication}`}
                    aria-label={`Remove ${medication}`}
                  >
                    <FaTimes size={11} />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div
              className="
                rounded-xl
                border
                border-dashed
                border-slate-300
                bg-white
                px-5
                py-7
                text-center
              "
            >
              <FaPills
                size={23}
                className="mx-auto mb-2 text-slate-300"
              />

              <p className="text-sm text-slate-500">
                No medications selected
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Search and add medications above.
              </p>
            </div>
          )}
        </section>

        {/* =====================================================
            ADD MEDICATION + ANALYZE
        ====================================================== */}
        <div
          className="
            mb-10
            flex
            flex-col
            gap-4
            sm:flex-row
            sm:items-center
            sm:justify-between
          "
        >
          <button
            type="button"
            onClick={handleAddMedication}
            className="
              flex
              items-center
              gap-2
              text-sm
              font-medium
              text-blue-600
              transition
              hover:text-blue-700
            "
          >
            <FaPlus size={11} />
            Add medication
          </button>

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={selectedMedications.length < 2}
            className="
              flex
              items-center
              justify-center
              gap-2
              rounded-xl
              bg-blue-600
              px-6
              py-3
              text-sm
              font-semibold
              text-white
              shadow-sm
              transition
              hover:bg-blue-700
              disabled:cursor-not-allowed
              disabled:bg-slate-300
            "
          >
            <FaPills size={14} />
            Analyze DDI
          </button>
        </div>

        {/* =====================================================
            ANALYSIS RESULT
            Only appears after Analyze DDI
        ====================================================== */}
        {hasAnalyzed && (
          <>
            {/* =================================================
                ANALYSIS SUMMARY
            ================================================== */}
            <section className="mb-10">
              <div className="mb-4">
                <h2 className="text-lg font-bold text-slate-800">
                  Analysis Summary
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Overview of the current DDI analysis
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                {/* DRUGS */}
                <SummaryCard
                  value={selectedMedications.length}
                  label="Drugs Analyzed"
                />

                {/* INTERACTIONS */}
                <SummaryCard
                  value={mockInteractions.length}
                  label="Interactions Identified"
                />

                {/* MAJOR */}
                <SummaryCard
                  value={majorCount}
                  label="Major"
                />

                {/* MODERATE */}
                <SummaryCard
                  value={moderateCount}
                  label="Moderate"
                />
              </div>
            </section>

            {/* =================================================
                DDI ANALYSIS RESULT
            ================================================== */}
            <section>
              <div className="mb-5">
                <h2 className="text-lg font-bold text-slate-800">
                  DDI Analysis Result
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  {selectedMedications.length} medications
                  analyzed · {mockInteractions.length}{" "}
                  potential interactions identified
                </p>
              </div>

              {/* INTERACTION CARDS */}
              <div className="space-y-5">
                {mockInteractions.map(
                  (interaction, index) => (
                    <InteractionCard
                      key={`${interaction.drug1}-${interaction.drug2}-${index}`}
                      interaction={interaction}
                      getSeverityClass={getSeverityClass}
                    />
                  )
                )}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}

/* =========================================================
   SUMMARY CARD
========================================================= */

function SummaryCard({
  value,
  label,
}: {
  value: number;
  label: string;
}) {
  return (
    <div
      className="
        flex
        min-h-[125px]
        flex-col
        items-center
        justify-center
        rounded-xl
        border
        border-slate-200
        bg-white
        px-4
        py-5
        text-center
        shadow-sm
      "
    >
      <span className="text-3xl font-bold text-blue-600">
        {value}
      </span>

      <span className="mt-2 max-w-[130px] text-sm font-medium leading-5 text-slate-500">
        {label}
      </span>
    </div>
  );
}

/* =========================================================
   INTERACTION CARD
========================================================= */

function InteractionCard({
  interaction,
  getSeverityClass,
}: {
  interaction: Interaction;
  getSeverityClass: (
    severity: Interaction["severity"]
  ) => string;
}) {
  return (
    <article
      className="
        overflow-hidden
        rounded-2xl
        border
        border-slate-200
        bg-white
        shadow-sm
      "
    >
      {/* DRUG PAIR HEADER */}
      <div className="border-b border-slate-200 px-5 py-4 md:px-6">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-bold tracking-wide text-slate-800">
            {interaction.drug1}
          </span>

          <span className="text-blue-500">↔</span>

          <span className="text-sm font-bold tracking-wide text-slate-800">
            {interaction.drug2}
          </span>
        </div>
      </div>

      {/* INTERACTION CONTENT */}
      <div className="p-5 md:p-6">
        {/* SEVERITY + SUMMARY */}
        <div className="mb-6">
          <span
            className={`
              inline-flex
              rounded-lg
              border
              px-3
              py-1.5
              text-xs
              font-bold
              tracking-wide
              ${getSeverityClass(interaction.severity)}
            `}
          >
            {interaction.severity}
          </span>

          <p className="mt-3 text-base font-semibold text-slate-700">
            {interaction.summary}
          </p>
        </div>

        {/* CLINICAL INTERPRETATION */}
        <div className="mb-5">
          <h3 className="mb-2 text-sm font-semibold text-slate-700">
            Clinical Interpretation
          </h3>

          <p className="text-sm leading-6 text-slate-500">
            {interaction.interpretation}
          </p>
        </div>

        {/* CLINICAL SIGNIFICANCE */}
        <div className="mb-6">
          <h3 className="mb-2 text-sm font-semibold text-slate-700">
            Clinical significance
          </h3>

          <p className="text-sm leading-6 text-slate-500">
            {interaction.significance}
          </p>
        </div>

        {/* FOOTER */}
        <div
          className="
            flex
            flex-col
            gap-4
            border-t
            border-slate-100
            pt-4
            sm:flex-row
            sm:items-center
            sm:justify-between
          "
        >
          {/* EVIDENCE */}
          <button
            type="button"
            className="
              flex
              items-center
              gap-2
              text-sm
              font-medium
              text-blue-600
              transition
              hover:text-blue-700
            "
          >
            <FaBook size={13} />

            <span>
              Evidence: {interaction.evidenceCount} sources
            </span>
          </button>

          {/* DETAILS */}
          <button
            type="button"
            className="
              flex
              items-center
              gap-2
              text-sm
              font-semibold
              text-blue-600
              transition
              hover:text-blue-700
            "
          >
            <span>Details</span>

            <FaChevronRight size={11} />
          </button>
        </div>
      </div>
    </article>
  );
}

