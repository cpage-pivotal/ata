import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Clock, Search, ThumbsUp, ThumbsDown, AlertTriangle, Info } from 'lucide-react';
import { queryService } from '@/services/api';
import { useAppStore } from '@/stores/appStore';
import ReactMarkdown from 'react-markdown';

export const Query: React.FC = () => {
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [feedbackSubmitted, setFeedbackSubmitted] = useState<string | null>(null);

    // Get state and actions from store
    const {
        queryHistory,
        currentQuery: storeQuery,
        currentResponse,
        queryLoading,
        queryError,
        setCurrentQuery: setStoreQuery,
        setCurrentResponse,
        setQueryLoading,
        setQueryError,
        setQueryHistory
    } = useAppStore();

    // Load suggestions on component mount
    useEffect(() => {
        const loadSuggestions = async () => {
            try {
                const suggestionsData = await queryService.getSuggestions();
                setSuggestions(suggestionsData);
            } catch (error) {
                console.error('Failed to load query suggestions:', error);
            }
        };

        loadSuggestions();
    }, []);

    const handleSubmitQuery = async (query: string) => {
        if (!query.trim()) return;

        setFeedbackSubmitted(null);

        try {
            setQueryLoading(true);
            setQueryError(null);

            console.log('Submitting query:', query);

            const response = await queryService.processQuery(query, {
                max_results: 10,
                include_sources: true,
                similarity_threshold: 0.5,
                temperature: 0.7,
                query_type: "auto"
            });

            setCurrentResponse(response);
            setStoreQuery(query);

            // Refresh query history
            try {
                const updatedHistory = await queryService.getHistory(10);
                setQueryHistory(updatedHistory);
            } catch (historyError) {
                console.warn('Failed to refresh query history:', historyError);
            }

            console.log('Query response received:', response);
        } catch (error: any) {
            console.error('Query failed:', error);
            const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
            setQueryError(`Query failed: ${errorMessage}`);
        } finally {
            setQueryLoading(false);
        }
    };

    const handleSuggestionClick = (suggestion: string) => {
        setStoreQuery(suggestion);
        handleSubmitQuery(suggestion);
    };

    const handleSubmitFeedback = async (helpful: boolean, queryId?: string) => {
        if (!currentResponse || !queryId) return;

        try {
            await queryService.submitFeedback(queryId, helpful);
            setFeedbackSubmitted(queryId);
            console.log('Feedback submitted successfully');
        } catch (error) {
            console.error('Failed to submit feedback:', error);
        }
    };

    return (
        <div className="space-y-6">
            {/* Query Input */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <Search className="h-5 w-5" />
                        <span>Natural Language Query</span>
                    </CardTitle>
                    <CardDescription>
                        Ask questions about maintenance reports using natural language
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex space-x-2">
                        <Input
                            placeholder="What issues do we see related to corrosion?"
                            value={storeQuery}
                            onChange={(e) => setStoreQuery(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmitQuery(storeQuery);
                                }
                            }}
                            className="flex-1"
                            disabled={queryLoading}
                        />
                        <Button
                            onClick={() => handleSubmitQuery(storeQuery)}
                            disabled={queryLoading || !storeQuery.trim()}
                        >
                            {queryLoading ? 'Processing...' : 'Query'}
                        </Button>
                    </div>

                    {/* Query Suggestions */}
                    {suggestions.length > 0 && !currentResponse && (
                        <div>
                            <p className="text-sm text-muted-foreground mb-2">Try these example queries:</p>
                            <div className="flex flex-wrap gap-2">
                                {suggestions.slice(0, 5).map((suggestion, index) => (
                                    <Button
                                        key={index}
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleSuggestionClick(suggestion)}
                                        disabled={queryLoading}
                                        className="text-xs"
                                    >
                                        {suggestion}
                                    </Button>
                                ))}
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Query Error */}
            {queryError && (
                <Card className="border-red-200 bg-red-50">
                    <CardContent className="pt-6">
                        <div className="flex items-center space-x-2 text-red-800">
                            <AlertTriangle className="h-4 w-4" />
                            <span className="text-sm font-medium">Query Error</span>
                        </div>
                        <p className="text-sm text-red-700 mt-2">{queryError}</p>
                    </CardContent>
                </Card>
            )}

            {/* Query Response */}
            {currentResponse && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Response</CardTitle>
                        <CardDescription className="flex items-center justify-between">
                            <span>Query: "{storeQuery}"</span>
                            <span className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span>{currentResponse.metadata.processing_time_ms}ms</span>
              </span>
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* Response Text */}
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                            <ReactMarkdown>{currentResponse.response}</ReactMarkdown>
                        </div>

                        {/* Metadata */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-muted/50 rounded-lg">
                            <div>
                                <p className="text-xs text-muted-foreground">Confidence</p>
                                <p className="font-medium">{Math.round(currentResponse.metadata.confidence_score * 100)}%</p>
                            </div>
                            <div>
                                <p className="text-xs text-muted-foreground">Sources</p>
                                <p className="font-medium">{currentResponse.metadata.total_sources_considered}</p>
                            </div>
                            <div>
                                <p className="text-xs text-muted-foreground">Query Type</p>
                                <p className="font-medium capitalize">{currentResponse.metadata.query_type}</p>
                            </div>
                            <div>
                                <p className="text-xs text-muted-foreground">Model</p>
                                <p className="font-medium">{currentResponse.metadata.model_used}</p>
                            </div>
                        </div>

                        {/* Sources */}
                        {currentResponse.sources.length > 0 && (
                            <div>
                                <h4 className="font-medium mb-3">Source Reports ({currentResponse.sources.length})</h4>
                                <div className="space-y-3">
                                    {currentResponse.sources.map((source, index) => (
                                        <div key={index} className="border rounded-lg p-4 space-y-2">
                                            <div className="flex items-start justify-between">
                                                <div className="space-y-1">
                                                    <p className="font-medium text-sm">{source.aircraft_model || 'Unknown Aircraft'}</p>
                                                    <p className="text-xs text-muted-foreground">
                                                        ATA {source.ata_chapter} {source.ata_chapter_name && `- ${source.ata_chapter_name}`}
                                                    </p>
                                                    <p className="text-xs text-muted-foreground">
                                                        Report ID: {source.report_id}
                                                    </p>
                                                </div>
                                                <div className="flex items-center space-x-2">
                          <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                            {Math.round(source.similarity_score * 100)}% match
                          </span>
                                                    {source.safety_critical && (
                                                        <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded flex items-center space-x-1">
                              <AlertTriangle className="h-3 w-3" />
                              <span>Safety Critical</span>
                            </span>
                                                    )}
                                                </div>
                                            </div>
                                            <p className="text-sm">{source.excerpt}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Feedback */}
                        <div className="border-t pt-4">
                            <p className="text-sm font-medium mb-2">Was this response helpful?</p>
                            {feedbackSubmitted === (currentResponse as any)?.query_id ? (
                                <p className="text-sm text-green-600">Thank you for your feedback!</p>
                            ) : (
                                <div className="flex space-x-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleSubmitFeedback(true, (currentResponse as any)?.query_id)}
                                        className="flex items-center space-x-1"
                                    >
                                        <ThumbsUp className="h-4 w-4" />
                                        <span>Helpful</span>
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleSubmitFeedback(false, (currentResponse as any)?.query_id)}
                                        className="flex items-center space-x-1"
                                    >
                                        <ThumbsDown className="h-4 w-4" />
                                        <span>Not Helpful</span>
                                    </Button>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Query History */}
            {queryHistory.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                            <Info className="h-5 w-5" />
                            <span>Recent Queries</span>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {queryHistory.slice(0, 5).map((query) => (
                                <div key={query.id} className="border rounded-lg p-3 space-y-2">
                                    <div className="flex items-start justify-between">
                                        <p className="text-sm font-medium">{query.query_text}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {new Date(query.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <p className="text-xs text-muted-foreground line-clamp-2">
                                        {query.response.substring(0, 150)}...
                                    </p>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => {
                                            setStoreQuery(query.query_text);
                                            handleSubmitQuery(query.query_text);
                                        }}
                                        className="text-xs"
                                    >
                                        Run Again
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default Query;