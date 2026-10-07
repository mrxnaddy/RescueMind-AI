import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const API_BASE_URL = "https://rescuemind-ai-production.up.railway.app";

const severityColors = {
  critical: "#dc2626",
  high: "#ea580c",
  medium: "#ca8a04",
  low: "#16a34a",
};

function createIncidentIcon(severity) {
  const color = severityColors[severity] || "#2563eb";

  return L.divIcon({
    className: "custom-incident-marker",
    html: `
      <div style="
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: ${color};
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.35);
      "></div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });
}

function MapController({ incidents }) {
  const map = useMap();

  useEffect(() => {
    if (incidents.length === 0) {
      return;
    }

    const validIncidents = incidents.filter(
      (incident) =>
        typeof incident.latitude === "number" &&
        typeof incident.longitude === "number"
    );

    if (validIncidents.length === 0) {
      return;
    }

    const bounds = L.latLngBounds(
      validIncidents.map((incident) => [
        incident.latitude,
        incident.longitude,
      ])
    );

    map.fitBounds(bounds, {
      padding: [50, 50],
      maxZoom: 14,
    });
  }, [incidents, map]);

  return null;
}

export default function Map() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/map/incidents`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Failed to load map incidents.");
        }

        return response.json();
      })
      .then((data) => {
        setIncidents(data.incidents || []);
      })
      .catch((err) => {
        setError(err.message || "Unable to load map data.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const filteredIncidents = useMemo(() => {
    return incidents.filter((incident) => {
      const severityMatch =
        severityFilter === "all" ||
        (incident.severity || "").toLowerCase() === severityFilter;

      const typeMatch =
        typeFilter === "all" ||
        (incident.emergency_type || "").toLowerCase() === typeFilter;

      const statusMatch =
        statusFilter === "all" ||
        (incident.status || "").toLowerCase() === statusMatch;

      return severityMatch && typeMatch && statusMatch;
    });
  }, [incidents, severityFilter, typeFilter, statusFilter]);

  const defaultCenter = [33.6844, 73.0479];

  const emergencyTypes = [
    ...new Set(
      incidents
        .map((incident) => incident.emergency_type)
        .filter(Boolean)
        .map((type) => type.toLowerCase())
    ),
  ];

  const statuses = [
    ...new Set(
      incidents
        .map((incident) => incident.status)
        .filter(Boolean)
        .map((status) => status.toLowerCase())
    ),
  ];

  function clearFilters() {
    setSeverityFilter("all");
    setTypeFilter("all");
    setStatusFilter("all");
  }

  return (
    <div className="flex h-full min-h-[calc(100vh-80px)] flex-col bg-slate-50">
      <div className="border-b bg-white px-6 py-4">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Emergency Map
              </h1>

              <p className="text-sm text-slate-500">
                Interactive view of simulated emergency incidents.
              </p>
            </div>

            <div className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700">
              {loading
                ? "Loading incidents..."
                : `${filteredIncidents.length} of ${incidents.length} incidents`}
            </div>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Severity
              </label>

              <select
                value={severityFilter}
                onChange={(event) =>
                  setSeverityFilter(event.target.value)
                }
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-slate-500"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Emergency Type
              </label>

              <select
                value={typeFilter}
                onChange={(event) => setTypeFilter(event.target.value)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-slate-500"
              >
                <option value="all">All Types</option>

                {emergencyTypes.map((type) => (
                  <option key={type} value={type}>
                    {type.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">
                Status
              </label>

              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-slate-500"
              >
                <option value="all">All Statuses</option>

                {statuses.map((status) => (
                  <option key={status} value={status}>
                    {status.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={clearFilters}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mx-6 mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="relative flex-1 p-4">
        <div className="h-[calc(100vh-250px)] min-h-[500px] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <MapContainer
            center={defaultCenter}
            zoom={6}
            scrollWheelZoom={true}
            className="h-full w-full"
          >
            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <MapController incidents={filteredIncidents} />

            {filteredIncidents.map((incident) => (
              <Marker
                key={incident.id}
                position={[incident.latitude, incident.longitude]}
                icon={createIncidentIcon(incident.severity)}
                eventHandlers={{
                  click: () => setSelectedIncident(incident),
                }}
              >
                <Popup>
                  <div className="min-w-[220px] space-y-2">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        {incident.title || "Emergency Incident"}
                      </h3>

                      <p className="text-xs text-slate-500">
                        {incident.incident_code}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="font-medium">Type:</span>{" "}
                        {incident.emergency_type}
                      </div>

                      <div>
                        <span className="font-medium">Severity:</span>{" "}
                        {incident.severity || "Unknown"}
                      </div>

                      <div>
                        <span className="font-medium">Status:</span>{" "}
                        {incident.status}
                      </div>

                      <div>
                        <span className="font-medium">Reports:</span>{" "}
                        {incident.report_count}
                      </div>
                    </div>

                    {incident.address && (
                      <div className="text-sm">
                        <span className="font-medium">Location:</span>{" "}
                        {incident.address}
                      </div>
                    )}

                    <div className="text-xs text-slate-500">
                      Coordinates: {incident.latitude},{" "}
                      {incident.longitude}
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>

        {selectedIncident && (
          <div className="absolute right-8 top-8 z-[1000] w-[320px] rounded-xl border border-slate-200 bg-white p-5 shadow-xl">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Selected Incident
                </p>

                <h2 className="mt-1 text-lg font-bold text-slate-900">
                  {selectedIncident.title || "Emergency Incident"}
                </h2>

                <p className="text-xs text-slate-500">
                  {selectedIncident.incident_code}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedIncident(null)}
                className="rounded-md px-2 py-1 text-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                aria-label="Close incident details"
              >
                ×
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between border-b pb-2">
                <span className="text-slate-500">Emergency Type</span>
                <span className="font-medium capitalize text-slate-800">
                  {(selectedIncident.emergency_type || "unknown").replaceAll(
                    "_",
                    " "
                  )}
                </span>
              </div>

              <div className="flex items-center justify-between border-b pb-2">
                <span className="text-slate-500">Severity</span>
                <span
                  className="font-semibold capitalize"
                  style={{
                    color:
                      severityColors[
                        (selectedIncident.severity || "").toLowerCase()
                      ] || "#475569",
                  }}
                >
                  {selectedIncident.severity || "Unknown"}
                </span>
              </div>

              <div className="flex items-center justify-between border-b pb-2">
                <span className="text-slate-500">Status</span>
                <span className="font-medium capitalize text-slate-800">
                  {(selectedIncident.status || "unknown").replaceAll(
                    "_",
                    " "
                  )}
                </span>
              </div>

              <div className="flex items-center justify-between border-b pb-2">
                <span className="text-slate-500">Reports</span>
                <span className="font-medium text-slate-800">
                  {selectedIncident.report_count ?? 0}
                </span>
              </div>

              {selectedIncident.address && (
                <div>
                  <p className="mb-1 text-slate-500">Location</p>
                  <p className="font-medium text-slate-800">
                    {selectedIncident.address}
                  </p>
                </div>
              )}

              <div>
                <p className="mb-1 text-slate-500">Coordinates</p>
                <p className="font-mono text-xs text-slate-700">
                  {selectedIncident.latitude}, {selectedIncident.longitude}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="absolute bottom-8 left-8 rounded-lg border border-slate-200 bg-white p-3 shadow-md">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Severity
          </p>

          <div className="space-y-1.5 text-xs">
            {Object.entries(severityColors).map(([severity, color]) => (
              <div key={severity} className="flex items-center gap-2">
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: color }}
                />

                <span className="capitalize text-slate-700">
                  {severity}
                </span>
              </div>
            ))}
          </div>
        </div>

        {!loading && filteredIncidents.length === 0 && !error && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <div className="rounded-lg bg-white px-5 py-4 text-center shadow-lg">
              <p className="font-semibold text-slate-800">
                No matching incidents
              </p>

              <p className="mt-1 text-sm text-slate-500">
                Try changing or clearing the filters.
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="border-t bg-white px-6 py-2 text-xs text-slate-500">
        Simulated incident data • AI-derived assessments are not verified
        emergency facts.
      </div>
    </div>
  );
}
