const Trades: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Trades
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            View your trading history and performance
          </p>
        </div>
      </div>

      {/* Placeholder for trades table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Trade History
          </h3>
          <div className="mt-2 text-sm text-gray-500">
            <p>No trades executed yet. Your trading history will appear here once the bot starts trading.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Trades;
