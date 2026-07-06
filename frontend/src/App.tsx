import { useEffect, useState } from "react";

import { AppHeader } from "./components/AppHeader";
import { PrototypeNotice } from "./components/PrototypeNotice";
import { DemoDataPage } from "./pages/DemoDataPage";
import { PatientDetailPage } from "./pages/PatientDetailPage";
import { PatientOverviewPage } from "./pages/PatientOverviewPage";

export function App() {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const handler = () => setPath(window.location.pathname);
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  const match = path.match(/^\/patients\/(\d+)$/);
  const isDemoData = path === "/demo-data";

  return (
    <>
      <AppHeader />
      <div className="container">
        {!match && !isDemoData && <PrototypeNotice />}
        {match ? <PatientDetailPage patientId={Number(match[1])} /> : isDemoData ? <DemoDataPage /> : <PatientOverviewPage />}
      </div>
    </>
  );
}
