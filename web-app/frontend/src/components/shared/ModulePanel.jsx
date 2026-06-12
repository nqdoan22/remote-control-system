import { useState } from "react";
import Applications from "../modules/Applications";
import Processes    from "../modules/Processes";
import Screenshot   from "../modules/Screenshot";
import LiveScreen   from "../modules/LiveScreen";
import KeyLogger    from "../modules/KeyLogger";
import FileDownload from "../modules/FileDownload";
import Webcam       from "../modules/Webcam";
import PowerControl from "../modules/PowerControl";

const MODULES = [
  { id: "applications", label: "Applications", component: Applications },
  { id: "processes",    label: "Processes",    component: Processes },
  { id: "screenshot",   label: "Screenshot",   component: Screenshot },
  { id: "livescreen",   label: "Live Screen",  component: LiveScreen },
  { id: "keylogger",    label: "Key Logger",   component: KeyLogger },
  { id: "filedownload", label: "File Download",component: FileDownload },
  { id: "webcam",       label: "Webcam",       component: Webcam },
  { id: "power",        label: "Power Control",component: PowerControl },
];

export default function ModulePanel({ selectedMachines }) {
  const [activeModule, setActiveModule] = useState("applications");
  const Active = MODULES.find(m => m.id === activeModule)?.component;

  return (
    <div className="module-panel">
      <div className="module-tabs">
        {MODULES.map(m => (
          <button
            key={m.id}
            className={activeModule === m.id ? "active" : ""}
            onClick={() => setActiveModule(m.id)}
          >
            {m.label}
          </button>
        ))}
      </div>
      <div className="module-content">
        {Active && <Active selectedMachines={selectedMachines} />}
      </div>
    </div>
  );
}
