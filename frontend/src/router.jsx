// Router configuration
// This file can be used for route constants and navigation helpers

export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  RUN_AGENT: '/run-agent',
  LEADS: '/leads',
  LEAD_DETAIL: '/leads/:id',
  METRICS: '/metrics',
};

// Navigation helpers
export const navigateToLead = (leadId) => `/leads/${leadId}`;
export const navigateToLeads = () => '/leads';
export const navigateToDashboard = () => '/dashboard';
export const navigateToRunAgent = () => '/run-agent';
export const navigateToMetrics = () => '/metrics';
