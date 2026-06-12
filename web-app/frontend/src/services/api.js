const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// TODO: Axios instance với JWT interceptor

export const authService = {
  login: (username, password) => {},
  logout: () => {},
}

export const machineService = {
  getMachines: () => {},
  getMachine: (id) => {},
}

export const moduleService = {
  getApplications: (machineId) => {},
  getProcesses: (machineId) => {},
  takeScreenshot: (machineId) => {},
  browseFiles: (machineId) => {},
  downloadFile: (machineId, path) => {},
  shutdown: (machineId) => {},
  sleep: (machineId) => {},
}
