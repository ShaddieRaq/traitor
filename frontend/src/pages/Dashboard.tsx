import PortfolioOverview from '../components/Portfolio/PortfolioOverview';
import MarketTicker from '../components/Market/MarketTicker';
import { useBotsStatus } from '../hooks/useBots';

const Dashboard: React.FC = () => {
  const { data: botsStatus } = useBotsStatus();
  const runningBots = botsStatus?.filter(bot => bot.status === 'RUNNING') || [];
  const hotBots = botsStatus?.filter(bot => bot.temperature === 'HOT') || [];
  const totalBots = botsStatus?.length || 0;
  
  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Monitor your trading bot performance and live portfolio
          </p>
        </div>
      </div>

      {/* Market Ticker */}
      <MarketTicker />

      {/* Status Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">●</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Running Bots
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {runningBots.length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">{totalBots}</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Bots
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {totalBots}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">🔥</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Hot Bots
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {hotBots.length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">$</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Coinbase Status
                  </dt>
                  <dd className="text-lg font-medium text-green-600">
                    Connected
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PortfolioOverview showMockData={false} />
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
                  View All Signals
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

          {/* Bot Status */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Bot Status
              </h3>
              <div className="space-y-3">
                {botsStatus?.slice(0, 3).map((bot) => (
                  <div key={bot.id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full ${bot.status === 'RUNNING' ? 'bg-green-500' : 'bg-gray-300'} mr-3`}></div>
                      <span className="text-sm font-medium text-gray-900">{bot.name}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`text-xs px-2 py-1 rounded-full ${bot.status === 'RUNNING' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                        {bot.status}
                      </span>
                      <span className="text-xs text-gray-500">
                        {bot.temperature === 'HOT' ? '🔥' : bot.temperature === 'WARM' ? '🌡️' : bot.temperature === 'COLD' ? '❄️' : '🧊'}
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
                <span className="text-sm text-gray-900">RSI Signal evaluated for BTC-USD</span>
              </div>
              <span className="text-xs text-gray-500">2 min ago</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-900">Market data updated</span>
              </div>
              <span className="text-xs text-gray-500">5 min ago</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-yellow-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-900">Moving Average Signal triggered</span>
              </div>
              <span className="text-xs text-gray-500">12 min ago</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
