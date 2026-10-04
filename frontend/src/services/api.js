import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
})

// Give every error a short, readable message.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail

    if (typeof detail === 'string') {
      error.userMessage = detail
    } else if (error.response) {
      error.userMessage = `Request failed (${error.response.status})`
    } else {
      error.userMessage = 'Cannot reach the server'
    }

    return Promise.reject(error)
  },
)

const get = (url, params) => api.get(url, { params }).then((r) => r.data)

// NOTE: list endpoints need the trailing slash, otherwise FastAPI redirects.
export const getHealth = () => get('/health')
export const getDatabaseHealth = () => get('/health/database')
export const getDashboardStats = () => get('/api/dashboard/stats')
export const getIncidents = (params) => get('/api/incidents/', params)
export const getIncident = (id) => get(`/api/incidents/${id}`)
export const getResources = (params) => get('/api/resources/', params)
export const getResourceSummary = () => get('/api/resources/summary')

export const getAssignments = (params) =>
  get('/api/assignments/', params)

export const releaseAssignment = (assignmentId, data = {}) =>
  api.post(`/api/assignments/${assignmentId}/release`, data).then((r) => r.data)

export const releaseIncidentAssignments = (incidentId, data = {}) =>
  api
    .post(`/api/assignments/incidents/${incidentId}/release-all`, data)
    .then((r) => r.data)

export const getResponsePlans = (incidentId) =>
  get(`/api/plans/incidents/${incidentId}`)

export const getResponsePlan = (planId) =>
  get(`/api/plans/${planId}`)

export const generateResponsePlan = (incidentId) =>
  api
    .post(`/api/plans/incidents/${incidentId}/generate`)
    .then((r) => r.data)

export const approveResponsePlan = (planId, data = {}) =>
  api
    .post(`/api/plans/${planId}/approve`, data)
    .then((r) => r.data)

export const rejectResponsePlan = (planId, data = {}) =>
  api
    .post(`/api/plans/${planId}/reject`, data)
    .then((r) => r.data)

export const getDuplicateCandidates = (params) =>
  get('/api/duplicates/candidates', params)

export const getDuplicateCandidate = (candidateId) =>
  get(`/api/duplicates/candidates/${candidateId}`)

export const confirmDuplicate = (candidateId, data = {}) =>
  api
    .post(`/api/duplicates/candidates/${candidateId}/confirm`, data)
    .then((r) => r.data)

export const rejectDuplicate = (candidateId, data = {}) =>
  api
    .post(`/api/duplicates/candidates/${candidateId}/reject`, data)
    .then((r) => r.data)

export const checkIncidentDuplicates = (incidentId) =>
  api
    .post(`/api/duplicates/incidents/${incidentId}/check`)
    .then((r) => r.data)

export const analyzeReport = (reportId) =>
  api
    .post(`/api/analysis/reports/${reportId}/analyze`)
    .then((r) => r.data)

export const runIntakeAnalysis = (reportId) =>
  api
    .post(`/api/analysis/reports/${reportId}/intake`)
    .then((r) => r.data)
export const getIncidentWorkflow = () =>
  get('/api/workflow/incident-statuses')

export const updateIncidentStatus = (incidentId, status, notes = '') =>
  api
    .patch(`/api/incidents/${incidentId}/status`, {
      status,
      notes: notes || null,
    })
    .then((r) => r.data)    
export const getIncidentAssignments = (incidentId) =>
  get('/api/assignments/', {
    incident_id: incidentId,
    status: 'assigned',
  })    
export const getIncidentHistory = (incidentId) =>
  get(`/api/incident-history/${incidentId}`)  