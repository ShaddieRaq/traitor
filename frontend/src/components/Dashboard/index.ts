// Phase 1 Dashboard Redesign Components
export { default as DashboardGrid, GridArea } from './DashboardGrid';
export { default as DashboardLayout } from './DashboardLayout';
export { default as PortfolioSummaryCard } from './PortfolioSummaryCard';
export { default as SystemHealthCard } from './SystemHealthCard';
export { default as HotBotsSection } from './HotBotsSection';
export { default as BotGridSection } from './BotGridSection';
export { default as UnifiedStatusBar } from './UnifiedStatusBar';

// Phase 2 Advanced Features
export { default as AdvancedFilterPanel } from './AdvancedFilterPanel';
export type { FilterCriteria } from './AdvancedFilterPanel';
export { default as MiniChart } from './MiniChart';
export { default as PerformanceTrend } from './PerformanceTrend';

// Re-export for easier importing
export * from './DashboardGrid';
