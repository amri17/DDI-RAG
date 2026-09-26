"use client";

export default function BerandaPage() {
  return (
    <div className="min-h-screen bg-slate-100 pt-24 px-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800">
          ICU-Q Dashboard
        </h1>

        <p className="mt-2 text-slate-500">
          Drug-Drug Interaction and Clinical Decision Support System
        </p>
      </div>

      {/* Statistik */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">
            Total Patients
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-800">
            0
          </p>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">
            Waiting
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-800">
            0
          </p>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">
            In Treatment
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-800">
            0
          </p>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">
            Closed
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-800">
            0
          </p>
        </div>
      </div>

      {/* Informasi Dashboard */}
      <div className="mt-8 rounded-xl bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-800">
          Dashboard Information
        </h2>

        <p className="mt-3 text-slate-500">
          This dashboard provides access to the ICU-Q clinical
          decision support system and Drug-Drug Interaction
          analysis features.
        </p>
      </div>
    </div>
  );
}

