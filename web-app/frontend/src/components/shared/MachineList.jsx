export default function MachineList({ machines, selectedMachines, onToggle }) {
  return (
    <div className="machine-list">
      <h2>Connected Machines</h2>
      {machines.length === 0 && <p>No machines connected.</p>}
      {machines.map(m => (
        <div
          key={m.id}
          className={`machine-item ${m.status} ${selectedMachines.includes(m.id) ? "selected" : ""}`}
          onClick={() => onToggle(m.id)}
        >
          <span>{m.name}</span>
          <span className={`badge ${m.status}`}>{m.status}</span>
        </div>
      ))}
    </div>
  );
}
