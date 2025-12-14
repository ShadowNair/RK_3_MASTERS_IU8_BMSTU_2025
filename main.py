import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
import os
from pathlib import Path
import hashlib
from fpdf import FPDF

warnings.filterwarnings('ignore')

# @file main.py
# @brief Modern IT Monitoring Dashboard (Dark Theme)
st.set_page_config(
    page_title="IT Monitoring Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# === НОВЫЙ СТИЛЬ (Dark theme + modern UI) ===
st.markdown("""
<style>
/* Общие настройки */
:root {
    --bg-primary: #0e1117;
    --bg-secondary: #161a25;
    --card-bg: #1e2130;
    --text-primary: #f0f2f6;
    --text-secondary: #a9b7c6;
    --accent-blue: #4e9af1;
    --accent-emerald: #00c896;
    --accent-orange: #ff9e44;
    --accent-red: #ff4b4b;
}

body, .main, .block-container {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background-color: var(--bg-primary);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
}

/* Заголовки */
h1, h2, h3, h4 {
    color: var(--text-primary) !important;
    font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
}

/* Метрики (st.metric) */
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
}

/* Кнопки */
button {
    border-radius: 8px !important;
    border: 1px solid #333 !important;
    background-color: var(--card-bg) !important;
    color: var(--text-primary) !important;
}
button:hover {
    background-color: #2a2e40 !important;
}

/* Карточки метрик */
.metric-card {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
}
.metric-card.critical {
    border-left: 4px solid var(--accent-red);
}
.metric-card.warning {
    border-left: 4px solid var(--accent-orange);
}
.metric-card.healthy {
    border-left: 4px solid var(--accent-emerald);
}

/* Главный заголовок */
.main-header {
    text-align: center;
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-emerald));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1.5rem;
}

/* Инпуты и селекты */
div[data-baseweb="select"], input {
    background-color: #262a39 !important;
    color: var(--text-primary) !important;
    border: 1px solid #333 !important;
}
</style>
""", unsafe_allow_html=True)

def hash_dataframe(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return ""
    hash_vals = pd.util.hash_pandas_object(df, index=True).values
    return hashlib.md5(hash_vals).hexdigest()[:12]

class ITMonitoringDashboard:
    def __init__(self):
        self.metrics_df = st.session_state.get('metrics_df')
        self.logs_df = st.session_state.get('logs_df')
        self.metrics_hash = st.session_state.get('metrics_hash')
        self.logs_hash = st.session_state.get('logs_hash')

    def generate_sample_metrics(self, save_to_disk=True):
        dates = pd.date_range('2025-01-15 08:00:00', periods=48, freq='5min')
        servers = ['web-server-01', 'db-server-01', 'app-server-01', 'cache-server-01']
        data = []
        for date in dates:
            for server in servers:
                base_cpu = 40 if 'web' in server else 60 if 'db' in server else 30
                cpu = np.clip(np.random.normal(base_cpu, 15), 5, 95)
                base_memory = 70 if 'app' in server else 50 if 'db' in server else 35
                memory = np.clip(np.random.normal(base_memory, 12), 15, 90)
                disk = np.clip(np.random.normal(60, 20), 25, 95)

                status = (
                    'critical' if cpu > 85 or memory > 85 or disk > 90 else
                    'warning' if cpu > 75 or memory > 75 or disk > 80 else
                    'healthy'
                )

                data.append({
                    'timestamp': date,
                    'server_name': server,
                    'cpu_percent': round(cpu, 1),
                    'memory_percent': round(memory, 1),
                    'disk_usage_percent': round(disk, 1),
                    'network_in_mbps': round(np.random.uniform(10, 200), 1),
                    'network_out_mbps': round(np.random.uniform(5, 150), 1),
                    'disk_io_read': np.random.randint(50, 1500),
                    'disk_io_write': np.random.randint(30, 1000),
                    'status': status
                })
        df = pd.DataFrame(data)
        if save_to_disk:
            path = DATA_DIR / "server_metrics.csv"
            df.to_csv(path, index=False)
            st.sidebar.success(f"✅ Метрики сохранены: `{path.name}`")
        return df

    def generate_sample_logs(self, save_to_disk=True):
        dates = pd.date_range('2025-01-15 08:00:00', periods=200, freq='30s')
        servers = ['web-server-01', 'app-server-01', 'db-server-01']
        endpoints = ['/api/users', '/api/products', '/api/orders', '/api/login',
                     '/api/health', '/api/reports', '/api/search', '/api/payment']
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        data = []

        for date in dates:
            server = np.random.choice(servers)
            endpoint = np.random.choice(endpoints)
            method = np.random.choice(methods)

            http_status = np.random.choice([200, 401, 404, 500, 503], p=[0.85, 0.08, 0.04, 0.02, 0.01])

            level = (
                'ERROR' if http_status >= 500 else
                'WARNING' if http_status >= 400 else
                np.random.choice(['INFO', 'DEBUG'], p=[0.8, 0.2])
            )

            response_time = (
                np.random.uniform(100, 500) if http_status >= 500 else
                np.random.uniform(50, 150) if 'db' in server else
                np.random.uniform(10, 80)
            )

            data.append({
                'timestamp': date,
                'level': level,
                'server_name': server,
                'client_ip': f"192.168.1.{np.random.randint(1, 255)}",
                'http_method': method,
                'endpoint': endpoint,
                'http_status': http_status,
                'response_time_ms': round(response_time),
                'user_agent': np.random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Chrome/120.0.0.0 Safari/537.36",
                    "Firefox/121.0",
                    "PostmanRuntime/7.0.0"
                ]),
                'message': f"{method} request to {endpoint} completed with status {http_status}"
            })
        df = pd.DataFrame(data)
        if save_to_disk:
            path = DATA_DIR / "web_app_logs.csv"
            df.to_csv(path, index=False)
            st.sidebar.success(f"✅ Логи сохранены: `{path.name}`")
        return df

    def load_data(self):
        st.sidebar.header("📁 Данные")

        metrics_path = DATA_DIR / "server_metrics.csv"
        logs_path = DATA_DIR / "web_app_logs.csv"

        # Загрузка или генерация метрик
        if metrics_path.exists():
            try:
                df = pd.read_csv(metrics_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                st.session_state['metrics_df'] = df
                st.session_state['metrics_hash'] = hash_dataframe(df)
            except Exception as e:
                st.sidebar.error(f"❌ Ошибка чтения метрик: {e}")
                df = self.generate_sample_metrics(save_to_disk=True)
                st.session_state['metrics_df'] = df
                st.session_state['metrics_hash'] = hash_dataframe(df)
        else:
            st.sidebar.info("🔄 Генерация метрик...")
            df = self.generate_sample_metrics(save_to_disk=True)
            st.session_state['metrics_df'] = df
            st.session_state['metrics_hash'] = hash_dataframe(df)

        if st.sidebar.button("🔄 Перегенерировать метрики"):
            df = self.generate_sample_metrics(save_to_disk=True)
            st.session_state['metrics_df'] = df
            st.session_state['metrics_hash'] = hash_dataframe(df)
            st.sidebar.success("✅ Метрики обновлены")

        # Загрузка или генерация логов
        if logs_path.exists():
            try:
                df = pd.read_csv(logs_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                st.session_state['logs_df'] = df
                st.session_state['logs_hash'] = hash_dataframe(df)
            except Exception as e:
                st.sidebar.error(f"❌ Ошибка чтения логов: {e}")
                df = self.generate_sample_logs(save_to_disk=True)
                st.session_state['logs_df'] = df
                st.session_state['logs_hash'] = hash_dataframe(df)
        else:
            st.sidebar.info("🔄 Генерация логов...")
            df = self.generate_sample_logs(save_to_disk=True)
            st.session_state['logs_df'] = df
            st.session_state['logs_hash'] = hash_dataframe(df)

        if st.sidebar.button("🔄 Перегенерировать логи"):
            df = self.generate_sample_logs(save_to_disk=True)
            st.session_state['logs_df'] = df
            st.session_state['logs_hash'] = hash_dataframe(df)
            st.sidebar.success("✅ Логи обновлены")

        self.metrics_df = st.session_state['metrics_df']
        self.logs_df = st.session_state['logs_df']
        self.metrics_hash = st.session_state['metrics_hash']
        self.logs_hash = st.session_state['logs_hash']

    def generate_pdf_report(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "IT Monitoring Report", ln=True, align='C')
        pdf.ln(10)

        metrics_count = len(self.metrics_df) if self.metrics_df is not None else 0
        logs_count = len(self.logs_df) if self.logs_df is not None else 0
        pdf.cell(0, 8, f"Metric records: {metrics_count}", ln=True)
        pdf.cell(0, 8, f"Log records: {logs_count}", ln=True)
        pdf.ln(5)

        # Инциденты
        incidents = []
        if self.metrics_df is not None and self.logs_df is not None:
            high_cpu = self.metrics_df[self.metrics_df['cpu_percent'] > 85]
            errors_5xx = self.logs_df[self.logs_df['http_status'] >= 500]
            for _, cpu_row in high_cpu.iterrows():
                t = cpu_row['timestamp']
                related = errors_5xx[
                    (errors_5xx['timestamp'] >= t - timedelta(minutes=2)) &
                    (errors_5xx['timestamp'] <= t + timedelta(minutes=2))
                ]
                if not related.empty:
                    incidents.append({
                        'timestamp': t.strftime('%Y-%m-%d %H:%M'),
                        'server': cpu_row['server_name'],
                        'cpu': cpu_row['cpu_percent'],
                        'errors': len(related)
                    })

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Detected Incidents", ln=True)
        pdf.set_font("Arial", size=10)
        if incidents:
            for inc in incidents[:5]:
                pdf.cell(0, 8, f"- {inc['timestamp']}: {inc['server']} | CPU: {inc['cpu']}% | Errors: {inc['errors']}", ln=True)
        else:
            pdf.cell(0, 8, "No incidents detected.", ln=True)

        if self.logs_df is not None:
            error_endpoints = self.logs_df[self.logs_df['http_status'] >= 500]['endpoint'].value_counts().head(3)
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Top Endpoints with 5xx Errors", ln=True)
            pdf.set_font("Arial", size=10)
            if not error_endpoints.empty:
                for ep, cnt in error_endpoints.items():
                    pdf.cell(0, 8, f"- {ep}: {cnt} errors", ln=True)
            else:
                pdf.cell(0, 8, "No 5xx errors found.", ln=True)

        pdf_data = pdf.output(dest='S')
        return pdf_data.encode('latin1')

    def show_metrics_dashboard(self):
        st.header("📊 Системные метрики")
        if self.metrics_df is None:
            st.warning("Нет данных. Загрузите или сгенерируйте.")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            servers = st.multiselect(
                "Серверы", self.metrics_df['server_name'].unique(),
                default=self.metrics_df['server_name'].unique()
            )
        with col2:
            min_date = self.metrics_df['timestamp'].min().date()
            max_date = self.metrics_df['timestamp'].max().date()
            date_range = st.date_input("Диапазон", [min_date, max_date])
        with col3:
            cpu_thresh = st.slider("CPU порог (%)", 0, 100, 80)
            mem_thresh = st.slider("RAM порог (%)", 0, 100, 75)

        filtered = self.metrics_df[
            (self.metrics_df['server_name'].isin(servers)) &
            (self.metrics_df['timestamp'].dt.date >= date_range[0]) &
            (self.metrics_df['timestamp'].dt.date <= date_range[1])
        ]
        if filtered.empty:
            st.error("Нет данных для выбранных фильтров.")
            return

        st.subheader("📈 Текущее состояние")

        # Определяем цвета для статусов
        status_colors = {
            'healthy': '#00c896',
            'warning': '#ff9e44',
            'critical': '#ff4b4b'
        }

        latest = filtered.sort_values('timestamp').groupby('server_name').last()
        cols = st.columns(len(latest))

        for i, (server, row) in enumerate(latest.iterrows()):
            # CPU
            cpu_val = row['cpu_percent']
            cpu_status = (
                'critical' if cpu_val > cpu_thresh else
                'warning' if cpu_val > cpu_thresh - 10 else
                'healthy'
            )
            cpu_color = status_colors[cpu_status]

            # RAM
            mem_val = row['memory_percent']
            mem_status = (
                'critical' if mem_val > mem_thresh else
                'warning' if mem_val > mem_thresh - 10 else
                'healthy'
            )
            mem_color = status_colors[mem_status]

            with cols[i]:
                # CPU Card
                st.markdown(f"""
                <div style="
                    background: #1e2130;
                    padding: 12px;
                    border-radius: 10px;
                    margin: 8px 0;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    border-left: 4px solid {cpu_color};
                ">
                    <div style="font-size:14px; color:#a9b7c6; margin-bottom:5px;">{server} CPU</div>
                    <div style="height:8px; background:#2a2e40; border-radius:4px; overflow:hidden; margin:5px 0;">
                        <div style="height:100%; width:{cpu_val}%; background:{cpu_color}; border-radius:4px;"></div>
                    </div>
                    <div style="font-size:20px; font-weight:bold; color:white;">{cpu_val:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

                # RAM Card
                st.markdown(f"""
                <div style="
                    background: #1e2130;
                    padding: 12px;
                    border-radius: 10px;
                    margin: 8px 0;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    border-left: 4px solid {mem_color};
                ">
                    <div style="font-size:14px; color:#a9b7c6; margin-bottom:5px;">{server} RAM</div>
                    <div style="height:8px; background:#2a2e40; border-radius:4px; overflow:hidden; margin:5px 0;">
                        <div style="height:100%; width:{mem_val}%; background:{mem_color}; border-radius:4px;"></div>
                    </div>
                    <div style="font-size:20px; font-weight:bold; color:white;">{mem_val:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.subheader("📉 История метрик")
        tabs = st.tabs(["CPU", "RAM", "Диск", "Сеть"])
        with tabs[0]:
            fig = px.line(filtered, x='timestamp', y='cpu_percent', color='server_name',
                          template="plotly_dark")
            fig.add_hline(y=cpu_thresh, line_dash="dash", line_color="#ff4b4b")
            st.plotly_chart(fig, use_container_width=True)
        with tabs[1]:
            fig = px.line(filtered, x='timestamp', y='memory_percent', color='server_name',
                          template="plotly_dark")
            fig.add_hline(y=mem_thresh, line_dash="dash", line_color="#ff4b4b")
            st.plotly_chart(fig, use_container_width=True)
        with tabs[2]:
            fig = px.line(filtered, x='timestamp', y='disk_usage_percent', color='server_name',
                          template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        with tabs[3]:
            fig = make_subplots(rows=2, cols=1, subplot_titles=("Входящий трафик", "Исходящий трафик"))
            for server in servers:
                sdata = filtered[filtered['server_name'] == server]
                fig.add_trace(go.Scatter(x=sdata['timestamp'], y=sdata['network_in_mbps'], name=f"{server} IN"), row=1, col=1)
                fig.add_trace(go.Scatter(x=sdata['timestamp'], y=sdata['network_out_mbps'], name=f"{server} OUT"), row=2, col=1)
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🌡️ Heatmap CPU (по времени)")
        heatmap_df = filtered.pivot_table(values='cpu_percent', index=filtered['timestamp'].dt.strftime('%H:%M'), columns='server_name', aggfunc='mean')
        fig = px.imshow(heatmap_df.T, aspect='auto', color_continuous_scale='Blues_r', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    def show_logs_analyzer(self):
        st.header("🔍 Анализ логов")
        if self.logs_df is None:
            st.warning("Нет данных логов.")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            servers = st.multiselect("Серверы", self.logs_df['server_name'].unique(), default=self.logs_df['server_name'].unique())
        with col2:
            levels = st.multiselect("Уровни", self.logs_df['level'].unique(), default=self.logs_df['level'].unique())
        with col3:
            query = st.text_input("Поиск по сообщению:")

        filtered = self.logs_df[
            (self.logs_df['server_name'].isin(servers)) &
            (self.logs_df['level'].isin(levels))
        ]
        if query:
            filtered = filtered[filtered['message'].str.contains(query, case=False, na=False)]
        if filtered.empty:
            st.error("Нет логов по фильтрам.")
            return

        st.subheader("📊 Статистика HTTP")
        status_counts = filtered['http_status'].value_counts().reset_index()
        status_counts.columns = ['http_status', 'count']
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            fig = px.pie(status_counts, values='count', names='http_status', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            total = len(filtered)
            success = len(filtered[filtered['http_status'] < 400])
            client_err = len(filtered[(filtered['http_status'] >= 400) & (filtered['http_status'] < 500)])
            server_err = len(filtered[filtered['http_status'] >= 500])
            st.metric("✅ Успешно", success)
            st.metric("⚠️ 4xx", client_err)
            st.metric("❌ 5xx", server_err)
        with col_c:
            avg_time = filtered['response_time_ms'].mean()
            err_rate = (server_err / total * 100) if total > 0 else 0
            st.metric("Всего", total)
            st.metric("⏱️ Среднее", f"{avg_time:.1f} мс")
            st.metric("📉 Ошибок", f"{err_rate:.1f}%")

        st.subheader("🔗 Эндпоинты")
        tabs = st.tabs(["Популярные", "Ошибки", "Производительность"])
        with tabs[0]:
            top = filtered.groupby('endpoint').size().nlargest(10)
            fig = px.bar(x=top.index, y=top.values, labels={'x': 'Эндпоинт', 'y': 'Запросы'}, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        with tabs[1]:
            errors = filtered[filtered['http_status'] >= 400]
            if not errors.empty:
                err_group = errors.groupby(['endpoint', 'http_status']).size().reset_index(name='count')
                fig = px.sunburst(err_group, path=['http_status', 'endpoint'], values='count', template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Ошибок не найдено.")
        with tabs[2]:
            slow = filtered.groupby('endpoint')['response_time_ms'].mean().nlargest(10)
            fig = px.bar(x=slow.index, y=slow.values, labels={'x': 'Эндпоинт', 'y': 'Среднее время (мс)'}, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Просмотр логов"):
            st.dataframe(filtered.sort_values('timestamp', ascending=False), use_container_width=True)
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Экспорт в CSV", csv, "logs_export.csv", "text/csv")

    def show_integration_analytics(self):
        st.header("🔍 Интеграционная аналитика")
        if self.metrics_df is None or self.logs_df is None:
            st.warning("Загрузите оба набора данных.")
            return

        server = st.selectbox("Сервер", self.metrics_df['server_name'].unique())
        m = self.metrics_df[self.metrics_df['server_name'] == server].copy()
        l = self.logs_df[self.logs_df['server_name'] == server].copy()

        # Объединение по времени (5-минутные интервалы)
        m['time_bin'] = m['timestamp'].dt.floor('5T')
        l['time_bin'] = l['timestamp'].dt.floor('5T')

        m_agg = m.groupby('time_bin').mean(numeric_only=True).reset_index()
        l_agg = l.groupby('time_bin').agg(
            request_count=('http_status', 'count'),
            avg_response_time=('response_time_ms', 'mean')
        ).reset_index()

        merged = pd.merge(m_agg, l_agg, on='time_bin', how='inner')
        if merged.empty:
            st.info("Недостаточно данных для анализа.")
            return

        corr_cpu_req = merged['cpu_percent'].corr(merged['request_count'])
        corr_mem_resp = merged['memory_percent'].corr(merged['avg_response_time'])

        col1, col2 = st.columns(2)
        with col1:
            fig = px.scatter(merged, x='request_count', y='cpu_percent', trendline='ols',
                             title=f"CPU vs Запросы (ρ = {corr_cpu_req:.2f})", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.scatter(merged, x='memory_percent', y='avg_response_time', trendline='ols',
                             title=f"RAM vs Время ответа (ρ = {corr_mem_resp:.2f})", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # Инциденты
        st.subheader("🚨 Обнаруженные инциденты")
        high_cpu = self.metrics_df[self.metrics_df['cpu_percent'] > 85]
        errors_5xx = self.logs_df[self.logs_df['http_status'] >= 500]
        incidents = []
        for _, cpu_row in high_cpu.iterrows():
            t = cpu_row['timestamp']
            related = errors_5xx[
                (errors_5xx['timestamp'] >= t - timedelta(minutes=2)) &
                (errors_5xx['timestamp'] <= t + timedelta(minutes=2))
            ]
            if not related.empty:
                incidents.append({
                    'timestamp': t,
                    'server': cpu_row['server_name'],
                    'cpu_usage': cpu_row['cpu_percent'],
                    'error_count': len(related),
                    'endpoints': ', '.join(related['endpoint'].unique())
                })

        if incidents:
            st.dataframe(pd.DataFrame(incidents), use_container_width=True)
        else:
            st.success("Инцидентов не обнаружено.")

        # Рекомендации
        st.subheader("💡 Рекомендации")
        slow_endpoints = self.logs_df.groupby('endpoint')['response_time_ms'].mean().nlargest(3)
        error_endpoints = self.logs_df[self.logs_df['http_status'] >= 500]['endpoint'].value_counts().head(3)

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Медленные эндпоинты:**")
            for ep, t in slow_endpoints.items():
                st.code(f"{ep}: {t:.1f} мс")
        with col2:
            st.write("**Ошибки 5xx:**")
            for ep, cnt in error_endpoints.items():
                st.code(f"{ep}: {cnt} ошибок")

        st.subheader("📄 Отчёт")
        if st.button("📄 Сгенерировать PDF"):
            pdf_bytes = self.generate_pdf_report()
            st.download_button("📥 Скачать PDF", pdf_bytes, "it_monitoring_report.pdf", "application/pdf")

def main():
    if 'metrics_df' not in st.session_state:
        st.session_state['metrics_df'] = None
    if 'logs_df' not in st.session_state:
        st.session_state['logs_df'] = None
    if 'metrics_hash' not in st.session_state:
        st.session_state['metrics_hash'] = None
    if 'logs_hash' not in st.session_state:
        st.session_state['logs_hash'] = None

    st.markdown('<h1 class="main-header">IT Monitoring Pro</h1>', unsafe_allow_html=True)
    app = ITMonitoringDashboard()
    app.load_data()

    page = st.sidebar.radio("🧭 Навигация", ["Системные метрики", "Анализ логов", "Интеграционная аналитика", "О проекте"])

    if page == "Системные метрики":
        app.show_metrics_dashboard()
    elif page == "Анализ логов":
        app.show_logs_analyzer()
    elif page == "Интеграционная аналитика":
        app.show_integration_analytics()
    else:
        st.subheader("ℹ️ О проекте")
        st.markdown("""
        **IT Monitoring Pro** — современный дашборд для DevOps и SRE.

        **Возможности:**
        - Реальное отслеживание серверных метрик
        - Глубокий анализ логов с фильтрацией
        - Корреляция нагрузки и ошибок
        - Автоматическое обнаружение инцидентов
        - Экспорт данных и PDF-отчёты

        **Технологии:**  
        `Python`, `Streamlit`, `Pandas`, `Plotly`, `FPDF`, `statsmodels`

        **Данные:**  
        Автоматически генерируются при первом запуске в папке `data/`.
        """)

if __name__ == "__main__":
    main()