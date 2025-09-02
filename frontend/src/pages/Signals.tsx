import { useState } from 'react';
import toast from 'react-hot-toast';
import { useBots, useDeleteBot, useStartBot, useStopBot, useCreateBot, useUpdateBot } from '../hooks/useBots';
import { Bot, BotCreate, BotUpdate } from '../types';
import BotForm from '../components/BotForm';

const Signals: React.FC = () => {
  const { data: bots, isLoading, error } = useBots();
  const deleteBot = useDeleteBot();
  const startBot = useStartBot();
  const stopBot = useStopBot();
  const createBot = useCreateBot();
  const updateBot = useUpdateBot();

  // Modal state
  const [showForm, setShowForm] = useState(false);
  const [editingBot, setEditingBot] = useState<Bot | null>(null);

  const handleStart = (id: number) => {
    const botToStart = bots?.find(bot => bot.id === id);
    const botName = botToStart?.name || `Bot ${id}`;
    
    startBot.mutate(id, {
      onSuccess: () => {
        toast.success(`Bot "${botName}" started successfully`);
      },
      onError: () => {
        toast.error(`Failed to start bot "${botName}"`);
      }
    });
  };

  const handleStop = (id: number) => {
    const botToStop = bots?.find(bot => bot.id === id);
    const botName = botToStop?.name || `Bot ${id}`;
    
    stopBot.mutate(id, {
      onSuccess: () => {
        toast.success(`Bot "${botName}" stopped successfully`);
      },
      onError: () => {
        toast.error(`Failed to stop bot "${botName}"`);
      }
    });
  };

  const handleDelete = (id: number) => {
    const botToDelete = bots?.find(bot => bot.id === id);
    const botName = botToDelete?.name || `Bot ${id}`;
    
    if (confirm(`Are you sure you want to delete "${botName}"?`)) {
      deleteBot.mutate(id, {
        onSuccess: () => {
          toast.success(`Bot "${botName}" deleted successfully`);
        },
        onError: (error) => {
          console.error('Failed to delete bot:', error);
          toast.error(`Failed to delete bot "${botName}". Please try again.`);
        }
      });
    }
  };

  const handleCreateBot = () => {
    setEditingBot(null);
    setShowForm(true);
  };

  const handleEditBot = (bot: Bot) => {
    setEditingBot(bot);
    setShowForm(true);
  };

  const handleFormSubmit = (data: BotCreate) => {
    if (editingBot) {
      // Convert BotCreate to BotUpdate format
      const updateData: BotUpdate = {
        name: data.name,
        max_positions: data.max_positions,
        stop_loss_pct: data.stop_loss_pct,
        take_profit_pct: data.take_profit_pct,
        signal_config: data.signal_config
      };
      
      updateBot.mutate(
        { id: editingBot.id, bot: updateData },
        {
          onSuccess: () => {
            setShowForm(false);
            setEditingBot(null);
          }
        }
      );
    } else {
      // Create new bot
      createBot.mutate(data, {
        onSuccess: () => {
          setShowForm(false);
        }
      });
    }
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingBot(null);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800">
          Error loading bots. Please check your API connection.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Trading Bots
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage your trading bots and their configurations
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={handleCreateBot}
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Bot
          </button>
        </div>
      </div>

      {/* Bots List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {bots && bots.length > 0 ? (
            bots.map((bot) => (
              <li key={bot.id}>
                <div className="px-4 py-4 flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                        bot.status === 'RUNNING' ? 'bg-green-100' : 'bg-gray-100'
                      }`}>
                        <span className={`text-sm font-medium ${
                          bot.status === 'RUNNING' ? 'text-green-800' : 'text-gray-500'
                        }`}>
                          {bot.name.substring(0, 2).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900">
                          {bot.name}
                        </p>
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          bot.status === 'RUNNING' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {bot.status}
                        </span>
                        <span className="ml-2 text-xs">
                          {bot.temperature === 'HOT' ? '🔥' : bot.temperature === 'WARM' ? '🌡️' : bot.temperature === 'COLD' ? '❄️' : bot.temperature === 'FROZEN' ? '🧊' : '⚪'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">
                        {bot.pair} • Score: {bot.current_combined_score.toFixed(2)}
                      </p>
                      <p className="text-xs text-gray-400">
                        Position Size: ${bot.position_size_usd}{bot.current_position_size > 0 ? ` • Active: ${bot.current_position_size}` : ''}{bot.distance_to_signal ? ` • Distance: ${bot.distance_to_signal.toFixed(2)}` : ''}
                      </p>
                      <div className="text-xs text-gray-400 mt-1">
                        Signals: {Object.entries(bot.signal_config || {}).map(([key, config]: [string, any]) => 
                          config && config.enabled ? `${key.toUpperCase()}(${config.weight})` : null
                        ).filter(Boolean).join(', ') || 'None'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleEditBot(bot)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Edit Bot"
                    >
                      <span className="sr-only">Edit</span>
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => bot.status === 'RUNNING' ? handleStop(bot.id) : handleStart(bot.id)}
                      className={`relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                        bot.status === 'RUNNING' ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200 ${
                          bot.status === 'RUNNING' ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      />
                    </button>
                    <button 
                      onClick={() => handleDelete(bot.id)}
                      className="text-red-400 hover:text-red-600"
                      title="Delete Bot"
                    >
                      <span className="sr-only">Delete</span>
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </li>
            ))
          ) : (
            <li className="px-4 py-8 text-center text-gray-500">
              No bots configured yet. Add your first bot to get started.
            </li>
          )}
        </ul>
      </div>

      {/* Bot Form Modal */}
      {showForm && (
        <BotForm
          bot={editingBot}
          onSubmit={handleFormSubmit}
          onCancel={handleFormCancel}
          isLoading={createBot.isPending || updateBot.isPending}
        />
      )}
    </div>
  );
};

export default Signals;
