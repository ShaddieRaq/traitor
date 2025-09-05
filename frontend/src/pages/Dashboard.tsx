import PortfolioOverview from '../components/Portfolio/PortfolioOverview';
import MarketTicker from '../components/Market/MarketTicker';
import { useBotsStatus } from '../hooks/useBots';
import { useSystemStatus, getSystemHealthColor, getServiceStatusText } from '../hooks/useSystemStatus';
import { DataFreshnessIndicator, PollingStatusIndicator } from '../components/DataFreshnessIndicators';

const Dashboard: React.FC = () => {
  const { data: botsStatus, isLoading, dataUpdatedAt, isFetching } = useBotsStatus();
  const { data: systemStatus } = useSystemStatus();
  const runningBots = botsStatus?.filter(bot => bot.status === 'RUNNING') || [];
  const hotBots = botsStatus?.filter(bot => bot.temperature === 'HOT') || [];
  const totalBots = botsStatus?.length || 0;
  
  return (
    <div className="space-y-6">
      {/* Global System Status Bar */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="text-sm font-medium text-gray-900">System Status:</div>
              <div className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${getSystemHealthColor(systemStatus)}`}></div>
                <span className={`text-sm ${systemStatus?.status === 'healthy' ? 'text-green-700' : systemStatus?.status === 'degraded' ? 'text-yellow-700' : 'text-red-700'}`}>
                  {getServiceStatusText(systemStatus)}
                </span>
              </div>
            </div>
            <div className="text-gray-300">|</div>
            <PollingStatusIndicator isPolling={!isLoading} interval={5000} />
            {systemStatus?.data_freshness?.market_data && (
              <>
                <div className="text-gray-300">|</div>
                <div className="flex items-center space-x-1">
                  <span className="text-xs text-gray-600">Market Data:</span>
                  <div className={`w-2 h-2 rounded-full ${systemStatus.data_freshness.market_data.healthy ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  <span className="text-xs text-gray-500">
                    {systemStatus.data_freshness.market_data.seconds_since_update 
                      ? `${Math.round(systemStatus.data_freshness.market_data.seconds_since_update)}s ago`
                      : 'No data'
                    }
                  </span>
                </div>
              </>
            )}
          </div>
          <div className="flex items-center space-x-4">
            <DataFreshnessIndicator 
              lastUpdated={new Date(dataUpdatedAt)} 
              showTimestamp={true}
              size="sm"
              freshThresholdSeconds={10}
              staleThresholdSeconds={30}
            />
            {isFetching && (
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm text-blue-600">Refreshing data...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Monitor your trading bot performance and live portfolio with real-time updates
          </p>
        </div>
      </div>

      {/* Market Ticker */}
      <MarketTicker />

      {/* Real-time Bot Temperature Monitor - With Data Flow Indicators */}
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="text-2xl">🌡️</div>
              </div>
              <div className="ml-5 flex-1 min-w-0">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Real-time Bot Temperature Monitor
                  </dt>
                  <dd className="mt-1 text-2xl font-semibold text-gray-900 whitespace-nowrap">
                    {totalBots} Bots • {runningBots.length} Running • {hotBots.length} Hot
                  </dd>
                </dl>
              </div>
            </div>
            
            {/* System Status Indicators */}
            <div className="flex flex-col space-y-2">
              <PollingStatusIndicator isPolling={!isLoading} interval={5000} />
              <DataFreshnessIndicator 
                lastUpdated={new Date(dataUpdatedAt)} 
                showTimestamp={true}
                freshThresholdSeconds={10}
                staleThresholdSeconds={30}
              />
              {isFetching && (
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-spin"></div>
                  <span className="text-xs text-gray-500">Updating...</span>
                </div>
              )}
            </div>
          </div>
          
          {/* Bot Status Cards with Data Freshness Indicators */}
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
            {botsStatus?.map((bot) => (
              <div key={`bot-${bot.id}-${bot.current_combined_score}`} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="text-sm font-medium text-gray-900">{bot.name}</h4>
                      <DataFreshnessIndicator 
                        lastUpdated={new Date(dataUpdatedAt)} 
                        size="sm"
                        freshThresholdSeconds={10}
                        staleThresholdSeconds={30}
                      />
                    </div>
                    <p className="text-xs text-gray-500">{bot.pair}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-xs px-2 py-1 rounded ${bot.status === 'RUNNING' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                      {bot.status}
                    </span>
                    <div className="flex items-center space-x-1">
                      <span className="text-2xl">
                        {bot.temperature === 'HOT' ? '🔥' : bot.temperature === 'WARM' ? '🌡️' : bot.temperature === 'COOL' ? '❄️' : '🧊'}
                      </span>
                      {/* Temperature change indicator - pulse if recently updated */}
                      {isFetching && (
                        <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse"></div>
                      )}
                    </div>
                  </div>
                </div>
                <div className="mt-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      Score: <span className="font-mono font-semibold">{bot.current_combined_score.toFixed(3)}</span>
                    </p>
                    <span className="text-xs text-gray-400">
                      {new Date(dataUpdatedAt).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">
                    Temperature: {bot.temperature} • Distance: {bot.distance_to_signal?.toFixed(2) || 'N/A'}
                  </p>
                </div>
              </div>
            )) || (
              <div className="text-sm text-gray-500">
                {isLoading ? 'Loading bot data...' : 'No bots found'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PortfolioOverview />
        </div>
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Quick Actions
              </h3>
              <div className="space-y-3">
                <button className="w-full bg-blue-600 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                  View All Bots
                </button>
                <button className="w-full bg-green-600 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-green-700 transition-colors">
                  Market Analysis
                </button>
                <button className="w-full bg-gray-100 text-gray-700 text-sm font-medium py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors">
                  Trade History
                </button>
              </div>
            </div>
          </div>

          {/* Bot Status Summary */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Bot Status Summary
              </h3>
              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="bg-green-50 p-3 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{runningBots.length}</div>
                  <div className="text-xs text-green-700">Running</div>
                </div>
                <div className="bg-blue-50 p-3 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{totalBots}</div>
                  <div className="text-xs text-blue-700">Total</div>
                </div>
                <div className="bg-red-50 p-3 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{hotBots.length}</div>
                  <div className="text-xs text-red-700">🔥 Hot</div>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">•</div>
                  <div className="text-xs text-purple-700">Connected</div>
                </div>
              </div>
              
              <div className="mt-4 space-y-2">
                {botsStatus?.slice(0, 3).map((bot) => (
                  <div key={bot.id} className="flex items-center justify-between text-sm">
                    <div className="flex items-center">
                      <div className={`w-2 h-2 rounded-full ${bot.status === 'RUNNING' ? 'bg-green-500' : 'bg-gray-300'} mr-2`}></div>
                      <span className="font-medium">{bot.name}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className={`text-xs px-2 py-1 rounded ${bot.status === 'RUNNING' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                        {bot.status}
                      </span>
                      <span className="text-sm">
                        {bot.temperature === 'HOT' ? '🔥' : bot.temperature === 'WARM' ? '🌡️' : bot.temperature === 'COOL' ? '❄️' : '🧊'}
                      </span>
                    </div>
                  </div>
                )) || (
                  <div className="text-sm text-gray-500">Loading bots...</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Recent Activity
          </h3>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-900">Bot signal evaluation complete</span>
              </div>
              <span className="text-xs text-gray-500">Live</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-900">Market data stream active</span>
              </div>
              <span className="text-xs text-gray-500">Live</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-orange-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-900">Temperature calculations updated</span>
              </div>
              <span className="text-xs text-gray-500">Live</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
