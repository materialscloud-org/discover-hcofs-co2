// The information accordions of the home page.
import { DoiBadge, McInfoAccordions } from "mc-react-library";

function AboutContent() {
  return (
    <p>
      We screen a database of more than 69,000 hypothetical covalent organic frameworks (COFs) for carbon capture,
      using parasitic energy as a metric. In order to compute CO<sub>2</sub>-framework interactions in molecular simulations, we
      develop a genetic algorithm to tune the charge equilibration method and derive accurate framework partial
      charges. Nearly 400 COFs are identified with parasitic energy lower than that of an amine scrubbing process using
      monoethanolamine; over 70 are better performers than the best experimental COFs; and several perform similarly
      to Mg-MOF-74. We analyze the effect of pore topology on carbon capture performance in order to guide development
      of improved carbon capture materials.
    </p>
  );
}

function HowToCiteContent() {
  return (
    <p>
      Please find the appropriate journal reference in{" "}
      <span className="inline-block align-middle">
        <DoiBadge doi_id="2020.0029/v1" label="Data DOI" />
      </span>
      .
    </p>
  );
}

const ACCORDIONS = [
  { title: "About", content: <AboutContent /> },
  { title: "How to cite", content: <HowToCiteContent /> },
];

/** The information accordions, one open at a time. */
export default function InfoAccordions() {
  return <McInfoAccordions items={ACCORDIONS} />;
}
