// The pages, with this app's config.
import { useSearchParams, useParams } from "react-router-dom";

import InfoAccordions from "../AccordionContent.jsx";
import { Failed, Loading } from "../common/Common.jsx";
import DetailView from "../common/DetailView.jsx";
import Explorer from "../common/Explorer.jsx";
import { useTable } from "../common/queries.js";
import { config } from "./config.js";

// The home page: the default figure, with the information accordions above it.
export function HomePage() {
  return (
    <div className="space-y-6">
      <div className="mx-auto max-w-4xl space-y-3 px-6 pt-6 sm:px-10">
        <p className="text-lg">
          A database of 70k two- and three-dimensional covalent organic frameworks, screened for carbon capture.
        </p>
        <InfoAccordions />
      </div>
      <div className="px-2 pb-6 sm:px-8">
        <FigurePage />
      </div>
    </div>
  );
}

/** the scatter plot, from the preset of the ?preset= parameter (default: the home page's figure) */
export function FigurePage() {
  const [params] = useSearchParams();
  const preset = params.get("preset") ?? config.defaultPreset;
  const { data, error, isPending } = useTable();
  if (isPending) return <Loading />;
  if (error) return <Failed error={error} />;
  // key: a link to another preset restarts the controls
  return <Explorer key={preset} config={config} table={data} preset={preset} />;
}

export function DetailPage() {
  const { name } = useParams();
  return <DetailView name={name} shardCount={config.shardCount} explore={config.explore} />;
}
