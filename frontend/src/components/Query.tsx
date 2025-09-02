import React, { useState, useEffect } from 'react';
import { useAppStore } from '@/stores/appStore';
import { queryService } from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  MessageSquare, 
  Send, 
  Loader2, 
  AlertCircle,
  Clock,
  ThumbsUp,
  ThumbsDown,
  ExternalLink,
  Lightbulb
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const Query: React.FC = () => {
  const {
    currentQuery,
    setCurrentQuery,
    currentResponse,
    setCurrentResponse,
    queryLoading,
    setQueryLoading,
    queryError,
    setQueryError,
    queryHistory,
    setQueryHistory
  } = useAppStore();

  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState<string>('');

  // Load suggestions and history on component mount
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [suggestionsData, historyData] = await Promise.all([
          queryService.getSuggestions(),
          queryService.getHistory(10)
        ]);
        setSuggestions(suggestionsData);
        setQueryHistory(historyData);
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    };

    loadInitialData();
  }, [setQueryHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = selectedSuggestion || currentQuery;
    if (!query.trim()) return;

    try {
      setQueryLoading(true);
      setQueryError(null);
      setCurrentQuery(query);

      const response = await queryService.processQuery(query.trim());
      setCurrentResponse(response);

      // Refresh history
      const updatedHistory = await queryService.getHistory(10);
      setQueryHistory(updatedHistory);

      // Clear selected suggestion
      setSelectedSuggestion('');

    } catch (error) {
      setQueryError(error instanceof Error ? error.message : 'Query failed');
    } finally {
      setQueryLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setSelectedSuggestion(suggestion);
    setCurrentQuery(suggestion);
  };

  const handleFeedback = async (rating: number) => {
    if (!currentResponse) return;
    
    try {
      await queryService.submitFeedback('current_query_id', rating);
      // Could show a toast notification here
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Query Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <MessageSquare className="mr-2 h-5 w-5" />
            Natural Language Query
          </CardTitle>
          <CardDescription>
            Ask questions about maintenance reports using natural language
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex space-x-2">
              <Input
                placeholder="Ask about maintenance issues, defects, or specific aircraft..."
                value={selectedSuggestion || currentQuery}
                onChange={(e) => {
                  setCurrentQuery(e.target.value);
                  setSelectedSuggestion('');
                }}
                disabled={queryLoading}
                className="flex-1"
              />
              <Button type="submit" disabled={queryLoading || (!currentQuery.trim() && !selectedSuggestion)}>
                {queryLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* Query Suggestions */}
            {suggestions.length > 0 && !currentResponse && (
              <div className="space-y-2">
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <Lightbulb className="h-4 w-4" />
                  <span>Try these example queries:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {suggestions.slice(0, 4).map((suggestion, index) => (
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
          </form>

          {queryError && (
            <div className="mt-4 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <p className="text-sm text-destructive font-medium">Query Error</p>
              </div>
              <p className="text-sm text-destructive/80 mt-1">{queryError}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Query Response */}
      {currentResponse && (
        <Card>
          <CardHeader>
            <CardTitle>Response</CardTitle>
            <CardDescription className="flex items-center space-x-4">
              <span>Query: "{currentQuery}"</span>
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
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium">Report {source.report_id}</span>
                          {source.ata_chapter && (
                            <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                              ATA {source.ata_chapter}
                            </span>
                          )}
                          {source.safety_critical && (
                            <span className="text-xs bg-destructive/10 text-destructive px-2 py-1 rounded">
                              Safety Critical
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-muted-foreground">
                            {Math.round(source.similarity_score * 100)}% match
                          </span>
                          <Button variant="ghost" size="sm">
                            <ExternalLink className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                      
                      <p className="text-sm text-muted-foreground">{source.excerpt}</p>
                      
                      <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                        {source.aircraft_model && (
                          <span>Aircraft: {source.aircraft_model}</span>
                        )}
                        <span>Severity: {source.severity}</span>
                        {source.ata_chapter_name && (
                          <span>{source.ata_chapter_name}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Feedback */}
            <div className="flex items-center justify-between pt-4 border-t">
              <p className="text-sm text-muted-foreground">Was this response helpful?</p>
              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFeedback(1)}
                >
                  <ThumbsUp className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFeedback(-1)}
                >
                  <ThumbsDown className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Query History */}
      {queryHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Queries</CardTitle>
            <CardDescription>Your recent query history</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {queryHistory.map((item, index) => (
                <div 
                  key={item.id || index} 
                  className="p-3 rounded-lg border cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => setCurrentQuery(item.query_text)}
                >
                  <p className="text-sm font-medium">{item.query_text}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(item.created_at).toLocaleString()}
                  </p>
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
