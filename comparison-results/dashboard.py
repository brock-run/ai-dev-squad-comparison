#!/usr/bin/env python3
"""
AI Dev Squad Comparison Dashboard

This module provides a web-based dashboard for visualizing benchmark results
across different AI agent orchestration frameworks.
"""

import os
import json
import glob
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dashboard")

# Default paths
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "comparison-results")
DEFAULT_RAW_DATA_DIR = os.path.join(DEFAULT_DATA_DIR, "raw_data")
DEFAULT_REPORTS_DIR = os.path.join(DEFAULT_DATA_DIR, "reports")
DEFAULT_VISUALIZATIONS_DIR = os.path.join(DEFAULT_DATA_DIR, "visualizations")

# Ensure directories exist
os.makedirs(DEFAULT_RAW_DATA_DIR, exist_ok=True)
os.makedirs(DEFAULT_REPORTS_DIR, exist_ok=True)
os.makedirs(DEFAULT_VISUALIZATIONS_DIR, exist_ok=True)

# Color scheme for frameworks
FRAMEWORK_COLORS = {
    "langgraph": "#1f77b4",  # blue
    "crewai": "#ff7f0e",     # orange
    "autogen": "#2ca02c",    # green
    "n8n": "#d62728",        # red
    "semantic_kernel": "#9467bd"  # purple
}

class ResultsLoader:
    """Loads and processes benchmark results."""
    
    def __init__(self, data_dir: str = DEFAULT_RAW_DATA_DIR):
        """
        Initialize the results loader.
        
        Args:
            data_dir: Directory containing benchmark result files.
        """
        self.data_dir = data_dir
    
    def load_all_results(self) -> List[Dict[str, Any]]:
        """
        Load all benchmark result files.
        
        Returns:
            List of result dictionaries.
        """
        result_files = glob.glob(os.path.join(self.data_dir, "*.json"))
        results = []
        
        for file_path in result_files:
            try:
                with open(file_path, 'r') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                logger.error(f"Error loading result file {file_path}: {e}")
        
        logger.info(f"Loaded {len(results)} result files")
        return results
    
    def create_dataframe(self, results: List[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Create a DataFrame from benchmark results.
        
        Args:
            results: List of result dictionaries. If None, loads all results.
            
        Returns:
            DataFrame containing benchmark metrics.
        """
        if results is None:
            results = self.load_all_results()
        
        if not results:
            return pd.DataFrame()
        
        # Extract metrics into flat structure
        data = []
        
        for result in results:
            row = {
                "framework": result.get("framework", "unknown"),
                "task": result.get("task", "unknown"),
                "timestamp": result.get("timestamp", ""),
            }
            
            # Add functional performance metrics
            for name, value in result.get("metrics", {}).get("functional_performance", {}).items():
                row[f"functional_{name}"] = value
            
            # Add resource efficiency metrics
            for name, value in result.get("metrics", {}).get("resource_efficiency", {}).items():
                row[f"resource_{name}"] = value
            
            # Add developer experience metrics
            for name, value in result.get("metrics", {}).get("developer_experience", {}).items():
                row[f"developer_{name}"] = value
            
            # Add integration capabilities metrics
            for name, value in result.get("metrics", {}).get("integration_capabilities", {}).items():
                row[f"integration_{name}"] = value
            
            data.append(row)
        
        return pd.DataFrame(data)


class DashboardApp:
    """Dash application for visualizing benchmark results."""
    
    def __init__(self, data_dir: str = DEFAULT_RAW_DATA_DIR):
        """
        Initialize the dashboard application.
        
        Args:
            data_dir: Directory containing benchmark result files.
        """
        self.data_dir = data_dir
        self.loader = ResultsLoader(data_dir)
        self.df = self.loader.create_dataframe()
        
        # Initialize Dash app
        self.app = dash.Dash(__name__, title="AI Dev Squad Comparison Dashboard")
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Set up the dashboard layout."""
        self.app.layout = html.Div([
            html.H1("AI Dev Squad Comparison Dashboard", style={"textAlign": "center"}),
            
            html.Div([
                html.Div([
                    html.H3("Filters"),
                    html.Label("Framework:"),
                    dcc.Dropdown(
                        id="framework-dropdown",
                        options=[{"label": f, "value": f} for f in sorted(self.df["framework"].unique())],
                        multi=True,
                        value=sorted(self.df["framework"].unique())
                    ),
                    html.Label("Task:"),
                    dcc.Dropdown(
                        id="task-dropdown",
                        options=[{"label": t, "value": t} for t in sorted(self.df["task"].unique())],
                        multi=True,
                        value=sorted(self.df["task"].unique())
                    ),
                    html.Button("Refresh Data", id="refresh-button", n_clicks=0),
                ], style={"width": "25%", "padding": "10px", "backgroundColor": "#f8f9fa", "borderRadius": "5px"}),
                
                html.Div([
                    html.H3("Summary Statistics"),
                    html.Div(id="summary-stats")
                ], style={"width": "70%", "padding": "10px", "backgroundColor": "#f8f9fa", "borderRadius": "5px"}),
            ], style={"display": "flex", "justifyContent": "space-between", "margin": "20px 0"}),
            
            html.Div([
                html.H3("Performance Comparison"),
                dcc.Tabs([
                    dcc.Tab(label="Execution Time", children=[
                        dcc.Graph(id="execution-time-graph")
                    ]),
                    dcc.Tab(label="Memory Usage", children=[
                        dcc.Graph(id="memory-usage-graph")
                    ]),
                    dcc.Tab(label="Token Usage", children=[
                        dcc.Graph(id="token-usage-graph")
                    ]),
                    dcc.Tab(label="Cost Estimation", children=[
                        dcc.Graph(id="cost-graph")
                    ]),
                ])
            ], style={"margin": "20px 0"}),
            
            html.Div([
                html.H3("Quality Metrics"),
                dcc.Graph(id="quality-metrics-graph")
            ], style={"margin": "20px 0"}),
            
            html.Div([
                html.H3("Detailed Results"),
                dash_table.DataTable(
                    id="results-table",
                    columns=[{"name": col, "id": col} for col in self.df.columns],
                    data=self.df.to_dict("records"),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "padding": "10px",
                        "whiteSpace": "normal",
                        "height": "auto"
                    },
                    style_header={
                        "backgroundColor": "#f8f9fa",
                        "fontWeight": "bold"
                    }
                )
            ], style={"margin": "20px 0"})
        ], style={"margin": "0 auto", "maxWidth": "1200px", "padding": "20px"})
    
    def setup_callbacks(self):
        """Set up the dashboard callbacks."""
        @self.app.callback(
            [Output("summary-stats", "children"),
             Output("execution-time-graph", "figure"),
             Output("memory-usage-graph", "figure"),
             Output("token-usage-graph", "figure"),
             Output("cost-graph", "figure"),
             Output("quality-metrics-graph", "figure"),
             Output("results-table", "data"),
             Output("results-table", "columns")],
            [Input("framework-dropdown", "value"),
             Input("task-dropdown", "value"),
             Input("refresh-button", "n_clicks")]
        )
        def update_dashboard(frameworks, tasks, n_clicks):
            # Refresh data if button clicked
            if n_clicks > 0:
                self.df = self.loader.create_dataframe()
            
            # Filter data
            filtered_df = self.df
            if frameworks:
                filtered_df = filtered_df[filtered_df["framework"].isin(frameworks)]
            if tasks:
                filtered_df = filtered_df[filtered_df["task"].isin(tasks)]
            
            # Generate summary statistics
            summary_stats = self.generate_summary_stats(filtered_df)
            
            # Generate graphs
            execution_time_fig = self.create_execution_time_graph(filtered_df)
            memory_usage_fig = self.create_memory_usage_graph(filtered_df)
            token_usage_fig = self.create_token_usage_graph(filtered_df)
            cost_fig = self.create_cost_graph(filtered_df)
            quality_fig = self.create_quality_metrics_graph(filtered_df)
            
            # Update table
            columns = [{"name": col, "id": col} for col in filtered_df.columns]
            data = filtered_df.to_dict("records")
            
            return summary_stats, execution_time_fig, memory_usage_fig, token_usage_fig, cost_fig, quality_fig, data, columns
    
    def generate_summary_stats(self, df: pd.DataFrame) -> html.Div:
        """
        Generate summary statistics from filtered data.
        
        Args:
            df: Filtered DataFrame.
            
        Returns:
            HTML Div containing summary statistics.
        """
        if df.empty:
            return html.Div("No data available")
        
        # Calculate summary statistics
        framework_count = df["framework"].nunique()
        task_count = df["task"].nunique()
        avg_execution_time = df["resource_execution_time_seconds"].mean()
        avg_memory = df["resource_peak_memory_mb"].mean() if "resource_peak_memory_mb" in df.columns else 0
        avg_tokens = df["resource_total_tokens"].mean() if "resource_total_tokens" in df.columns else 0
        avg_cost = df["resource_estimated_cost_usd"].mean() if "resource_estimated_cost_usd" in df.columns else 0
        
        # Create summary cards
        return html.Div([
            html.Div([
                html.H4(f"{framework_count}"),
                html.P("Frameworks")
            ], style={"width": "20%", "textAlign": "center", "padding": "10px", "backgroundColor": "#e9ecef", "borderRadius": "5px"}),
            
            html.Div([
                html.H4(f"{task_count}"),
                html.P("Tasks")
            ], style={"width": "20%", "textAlign": "center", "padding": "10px", "backgroundColor": "#e9ecef", "borderRadius": "5px"}),
            
            html.Div([
                html.H4(f"{avg_execution_time:.2f}s"),
                html.P("Avg. Execution Time")
            ], style={"width": "20%", "textAlign": "center", "padding": "10px", "backgroundColor": "#e9ecef", "borderRadius": "5px"}),
            
            html.Div([
                html.H4(f"{avg_memory:.2f} MB"),
                html.P("Avg. Memory Usage")
            ], style={"width": "20%", "textAlign": "center", "padding": "10px", "backgroundColor": "#e9ecef", "borderRadius": "5px"}),
            
            html.Div([
                html.H4(f"${avg_cost:.4f}"),
                html.P("Avg. Cost")
            ], style={"width": "20%", "textAlign": "center", "padding": "10px", "backgroundColor": "#e9ecef", "borderRadius": "5px"}),
        ], style={"display": "flex", "justifyContent": "space-between"})
    
    def create_execution_time_graph(self, df: pd.DataFrame) -> go.Figure:
        """
        Create execution time comparison graph.
        
        Args:
            df: Filtered DataFrame.
            
        Returns:
            Plotly figure.
        """
        if df.empty or "resource_execution_time_seconds" not in df.columns:
            return go.Figure().update_layout(title="No execution time data available")
        
        # Group by framework and task
        grouped = df.groupby(["framework", "task"])["resource_execution_time_seconds"].mean().reset_index()
        
        # Create figure
        fig = px.bar(
            grouped,
            x="task",
            y="resource_execution_time_seconds",
            color="framework",
            barmode="group",
            title="Execution Time by Framework and Task",
            labels={"resource_execution_time_seconds": "Execution Time (seconds)", "task": "Task", "framework": "Framework"},
            color_discrete_map=FRAMEWORK_COLORS
        )
        
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Execution Time (seconds)",
            legend_title="Framework",
            plot_bgcolor="white"
        )
        
        return fig
    
    def create_memory_usage_graph(self, df: pd.DataFrame) -> go.Figure:
        """
        Create memory usage comparison graph.
        
        Args:
            df: Filtered DataFrame.
            
        Returns:
            Plotly figure.
        """
        if df.empty or "resource_peak_memory_mb" not in df.columns:
            return go.Figure().update_layout(title="No memory usage data available")
        
        # Group by framework and task
        grouped = df.groupby(["framework", "task"])["resource_peak_memory_mb"].mean().reset_index()
        
        # Create figure
        fig = px.bar(
            grouped,
            x="task",
            y="resource_peak_memory_mb",
            color="framework",
            barmode="group",
            title="Memory Usage by Framework and Task",
            labels={"resource_peak_memory_mb": "Peak Memory (MB)", "task": "Task", "framework": "Framework"},
            color_discrete_map=FRAMEWORK_COLORS
        )
        
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Peak Memory (MB)",
            legend_title="Framework",
            plot_bgcolor="white"
        )
        
        return fig
    
    def create_token_usage_graph(self, df: pd.DataFrame) -> go.Figure:
        """
        Create token usage comparison graph.
        
        Args:
            df: Filtered DataFrame.
            
        Returns:
            Plotly figure.
        """
        if df.empty or "resource_total_tokens" not in df.columns:
            return go.Figure().update_layout(title="No token usage data available")
        
        # Group by framework and task
        grouped = df.groupby(["framework", "task"])["resource_total_tokens"].mean().reset_index()
        
        # Create figure
        fig = px.bar(
            grouped,
            x="task",
            y="resource_total_tokens",
            color="framework",
            barmode="group",
            title="Token Usage by Framework and Task",
            labels={"resource_total_tokens": "Total Tokens", "task": "Task", "framework": "Framework"},
            color_discrete_map=FRAMEWORK_COLORS
        )
        
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Total Tokens",
            legend_title="Framework",
            plot_bgcolor="white"
        )
        
        return fig
    
    def create_cost_graph(self, df: pd.DataFrame) -> go.Figure:
        """
        Create cost comparison graph.
        
        Args:
            df: Filtered DataFrame.
            
        Returns:
            Plotly figure.
        """
        if df.empty or "resource_estimated_cost_usd" not in df.columns:
            return go.Figure().update_layout(title="No cost data available")
        
        # Group by framework and task
        grouped = df.groupby(["framework", "task"])["resource_estimated_cost_usd"].mean().reset_index()
        
        # Create figure
        fig = px.bar(
            grouped,
            x="task",
            y="resource_estimated_cost_usd",
            color="framework",
            barmode="group",
            title="Estimated Cost by Framework and Task",
            labels={"resource_estimated_cost_usd": "Estimated Cost (USD)", "task": "Task", "framework": "Framework"},
            color_discrete_map=FRAMEWORK_COLORS
        )
        
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Estimated Cost (USD)",
            legend_title="Framework",
            plot_bgcolor="white"
        )
        
        return fig
    
    def create_quality_metrics_graph(self, df: pd.DataFrame) -> go.Figure:
        """
        Create quality metrics comparison graph.
        
        Args:
            df: Filtered DataFrame.
            
        Returns:
            Plotly figure.
        """
        if df.empty or "functional_output_quality" not in df.columns:
            return go.Figure().update_layout(title="No quality metrics data available")
        
        # Group by framework and task
        grouped = df.groupby(["framework", "task"])["functional_output_quality"].mean().reset_index()
        
        # Create figure
        fig = px.bar(
            grouped,
            x="task",
            y="functional_output_quality",
            color="framework",
            barmode="group",
            title="Output Quality by Framework and Task",
            labels={"functional_output_quality": "Output Quality (1-10)", "task": "Task", "framework": "Framework"},
            color_discrete_map=FRAMEWORK_COLORS
        )
        
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Output Quality (1-10)",
            legend_title="Framework",
            plot_bgcolor="white"
        )
        
        return fig
    
    def run(self, debug: bool = False, port: int = 8050):
        """
        Run the dashboard application.
        
        Args:
            debug: Whether to run in debug mode.
            port: Port to run the server on.
        """
        self.app.run_server(debug=debug, port=port)


def main():
    """Main function to run the dashboard."""
    parser = argparse.ArgumentParser(description="AI Dev Squad Comparison Dashboard")
    parser.add_argument("--data-dir", default=DEFAULT_RAW_DATA_DIR, help="Directory containing benchmark result files")
    parser.add_argument("--port", type=int, default=8050, help="Port to run the dashboard on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    logger.info(f"Starting dashboard with data from {args.data_dir}")
    
    dashboard = DashboardApp(args.data_dir)
    dashboard.run(debug=args.debug, port=args.port)


if __name__ == "__main__":
    main()