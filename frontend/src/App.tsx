import { useState } from 'react';

function App() {
    const [activeView, setActiveView] = useState('dashboard');

    const navigation = [
        { id: 'dashboard', label: 'Dashboard' },
        { id: 'upload', label: 'Upload' },
        { id: 'query', label: 'Query' },
        { id: 'reports', label: 'Reports' },
    ];

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-4">
                        <div className="flex items-center">
                            <div className="bg-blue-600 p-2 rounded-lg mr-3">
                                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M21 16v-2l-8-5V3.5c0-.6-.4-1-1-1s-1 .4-1 1V9l-8 5v2l8-2.5V19l-2 1.5V22l3-1 3 1v-1.5L13 19v-5.5l8 2.5z"/>
                                </svg>
                            </div>
                            <div>
                                <h1 className="text-xl font-semibold text-slate-900">
                                    Boeing Aircraft Maintenance System
                                </h1>
                                <p className="text-sm text-slate-600">
                                    AI-Powered Maintenance Report Management
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Navigation */}
                <nav className="mb-8">
                    <div className="border-b border-slate-200">
                        <ul className="flex space-x-8">
                            {navigation.map((item) => (
                                <li key={item.id}>
                                    <button
                                        onClick={() => setActiveView(item.id)}
                                        className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                                            activeView === item.id
                                                ? 'border-blue-500 text-blue-600'
                                                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                                        }`}
                                    >
                                        {item.label}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>
                </nav>

                {/* Content */}
                <main>
                    {activeView === 'dashboard' && (
                        <div className="bg-white rounded-lg shadow p-6">
                            <h2 className="text-2xl font-bold text-slate-900 mb-4">Dashboard</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                                <div className="bg-slate-50 p-4 rounded-lg">
                                    <h3 className="font-semibold text-slate-900 mb-2">Total Reports</h3>
                                    <p className="text-3xl font-bold text-blue-600">0</p>
                                </div>
                                <div className="bg-slate-50 p-4 rounded-lg">
                                    <h3 className="font-semibold text-slate-900 mb-2">Safety Critical</h3>
                                    <p className="text-3xl font-bold text-red-600">0</p>
                                </div>
                                <div className="bg-slate-50 p-4 rounded-lg">
                                    <h3 className="font-semibold text-slate-900 mb-2">Aircraft Models</h3>
                                    <p className="text-3xl font-bold text-green-600">0</p>
                                </div>
                                <div className="bg-slate-50 p-4 rounded-lg">
                                    <h3 className="font-semibold text-slate-900 mb-2">Recent Reports</h3>
                                    <p className="text-3xl font-bold text-orange-600">0</p>
                                </div>
                            </div>
                            <p className="text-slate-600">
                                Welcome to the Boeing Aircraft Maintenance Report System. Upload your maintenance reports to get started!
                            </p>
                        </div>
                    )}

                    {activeView === 'upload' && (
                        <div className="bg-white rounded-lg shadow p-6">
                            <h2 className="text-2xl font-bold text-slate-900 mb-4">Upload Reports</h2>
                            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center">
                                <div className="mx-auto w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                                    <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                    </svg>
                                </div>
                                <p className="text-lg font-medium text-slate-900 mb-2">Upload maintenance reports</p>
                                <p className="text-slate-600 mb-4">Drag and drop your files here, or click to browse</p>
                                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                                    Choose Files
                                </button>
                            </div>
                        </div>
                    )}

                    {activeView === 'query' && (
                        <div className="bg-white rounded-lg shadow p-6">
                            <h2 className="text-2xl font-bold text-slate-900 mb-4">Ask Questions</h2>
                            <div className="mb-4">
                <textarea
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={4}
                    placeholder="Ask a question about your maintenance reports..."
                />
                            </div>
                            <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                                Ask Question
                            </button>
                        </div>
                    )}

                    {activeView === 'reports' && (
                        <div className="bg-white rounded-lg shadow p-6">
                            <h2 className="text-2xl font-bold text-slate-900 mb-4">Maintenance Reports</h2>
                            <p className="text-slate-600">
                                No maintenance reports uploaded yet. Use the Upload tab to add reports to the system.
                            </p>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}

export default App;