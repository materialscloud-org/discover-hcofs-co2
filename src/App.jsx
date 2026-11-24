import "./index.css";
import MaterialsCloudHeader from "mc-react-header";
import { McAppHeader } from "mc-react-library";
import { Link, Navigate, Route, Routes, useMatch } from "react-router-dom";

import { BackButton } from "./common/Common.jsx";
import { config } from "./HcofsExplorer/config.js";
import { DetailPage, FigurePage, HomePage } from "./HcofsExplorer/Pages.jsx";

// The routes: / (the home page, with the default figure), /figure?preset=<key>
// (the figure alone, as the old app's /figure) and /detail/<name>, relative to
// where the app is served.
export default function App() {
  const home = useMatch("/");
  const onFigure = useMatch("/figure");
  const name = useMatch("/detail/:name")?.params.name;
  return (
    <>
      <MaterialsCloudHeader
        activeSection="discover"
        breadcrumbsPath={[
          { name: "Discover", link: "https://www.materialscloud.org/discover" },
          { name: config.title, link: home ? null : import.meta.env.BASE_URL },
          ...(onFigure ? [{ name: "Interactive plot", link: null }] : []),
          ...(name ? [{ name, link: null }] : []),
        ]}
      />
      <main className="min-h-screen bg-[aliceblue] pb-10">
        <div className="mx-auto max-w-7xl px-4">
          <div className="overflow-hidden bg-white p-4 shadow-sm">
            <McAppHeader
              title={
                <Link to="/" className="text-inherit hover:no-underline">
                  {config.title}
                </Link>
              }
              logo={`${import.meta.env.BASE_URL}hcofs-co2.png`}
              logoAlt="Hypothetical COFs for CO2 capture logo"
              dois={config.dois}
            />
            <div className="mt-4 px-4">
              {!home && (
                <div className="mb-3">
                  <BackButton />
                </div>
              )}
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/figure" element={<FigurePage />} />
                <Route path="/detail/:name" element={<DetailPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
