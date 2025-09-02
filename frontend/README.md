# Boeing ATA System - Frontend

A modern React frontend for the Boeing Aircraft Maintenance Report Management System.

## Features

- **Dashboard**: Real-time statistics and analytics for maintenance reports
- **Upload Interface**: Drag-and-drop file upload with batch processing
- **Query System**: Natural language queries with RAG-powered responses
- **Reports Browser**: Search, filter, and view maintenance reports
- **Responsive Design**: Modern UI with Tailwind CSS and Shadcn/ui components

## Technology Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Shadcn/ui** for UI components
- **Zustand** for state management
- **Axios** for API communication
- **React Dropzone** for file uploads
- **React Markdown** for response rendering
- **Lucide React** for icons

## Getting Started

### Prerequisites

- Node.js 20+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp env.example .env.local
```

3. Configure environment variables:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building

Build for production:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Project Structure

```
src/
├── components/           # React components
│   ├── ui/              # Reusable UI components
│   ├── Dashboard.tsx    # Dashboard view
│   ├── Upload.tsx       # File upload interface
│   ├── Query.tsx        # Natural language query interface
│   ├── Reports.tsx      # Reports browser
│   └── Layout.tsx       # Main layout component
├── services/            # API services
│   └── api.ts          # Backend API client
├── stores/             # State management
│   └── appStore.ts     # Zustand store
├── lib/                # Utilities
│   └── utils.ts        # Helper functions
├── App.tsx             # Main application component
├── main.tsx            # Application entry point
└── index.css           # Global styles
```

## API Integration

The frontend integrates with the FastAPI backend through the following endpoints:

### Reports API
- `POST /api/reports/upload` - Batch file upload
- `POST /api/reports/ingest` - Single report ingestion
- `GET /api/reports/` - List reports with pagination
- `GET /api/reports/{id}` - Get specific report
- `POST /api/reports/search` - Semantic search
- `GET /api/reports/stats/summary` - Report statistics

### Query API
- `POST /api/query` - Process natural language queries
- `GET /api/query/history` - Query history
- `GET /api/query/suggestions` - Query suggestions
- `POST /api/query/feedback` - Submit feedback

### Health API
- `GET /api/health` - Basic health check
- `GET /api/health/detailed` - Detailed system status

## Features Overview

### Dashboard
- Real-time statistics display
- ATA chapter breakdown
- Severity distribution charts
- Aircraft model analytics
- Safety-critical report tracking

### Upload Interface
- Drag-and-drop file upload
- Single report entry form
- Real-time progress tracking
- Batch processing results
- Upload guidelines and validation

### Query System
- Natural language input
- RAG-powered responses
- Source citation display
- Query suggestions
- Response feedback system
- Query history tracking

### Reports Browser
- Paginated report listing
- Advanced search and filtering
- Report detail view
- ATA chapter filtering
- Severity-based filtering
- Aircraft model filtering

## State Management

The application uses Zustand for state management with the following stores:

- **Reports State**: Report data, statistics, loading states
- **Query State**: Query history, current query, responses
- **Upload State**: Upload progress, results, error handling
- **UI State**: Navigation, sidebar, current view

## Styling

The application uses Tailwind CSS with a custom design system:

- **Colors**: CSS variables for theme consistency
- **Components**: Shadcn/ui component library
- **Responsive**: Mobile-first responsive design
- **Dark Mode**: Support for light/dark themes

## Development Guidelines

### Code Style
- TypeScript strict mode enabled
- ESLint configuration for code quality
- Consistent import organization
- Component-based architecture

### API Integration
- Centralized API client with interceptors
- Type-safe API responses
- Error handling and loading states
- Request/response logging

### State Management
- Centralized state with Zustand
- Immutable state updates
- Type-safe store definitions
- Separation of concerns

## Deployment

The frontend can be deployed to any static hosting service:

1. Build the application:
```bash
npm run build
```

2. Deploy the `dist/` folder to your hosting service

### Environment Variables

Configure the following environment variables for deployment:

- `VITE_API_BASE_URL`: Backend API URL

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for new features
3. Update documentation for API changes
4. Test components thoroughly
5. Ensure responsive design compatibility

## License

This project is part of the Boeing Aircraft Maintenance Report System.