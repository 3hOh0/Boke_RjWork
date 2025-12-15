// 独立页面版本 - 每个页面独立加载数据
// 全局变量存储图表实例
let charts = {
  trend: null,
  likeTrend: null,
  favoriteTrend: null,
  commentTrend: null,
  category: null,
  tag: null
};

// 工具函数：异步获取JSON数据
async function fetchJSON(url) {
  const res = await fetch(url, { credentials: "same-origin" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// 通用图表配置
const chartDefaults = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: {
        padding: 15,
        font: { size: 12, weight: '600' },
        usePointStyle: true,
        pointStyle: 'circle'
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      titleFont: { size: 14, weight: 'bold' },
      bodyFont: { size: 13 },
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: true
    }
  }
};

// ==================== 内容分析页面 ====================
// 文章发布趋势图
async function loadTrendChart(days = 7) {
  try {
    const data = await fetchJSON(`/dashboard/api/trend/?range=${days}`);
    const labels = data.map(r => r.day);
    const values = data.map(r => r.published_count);
    
    const ctx = document.getElementById("trend-chart").getContext("2d");
    if (charts.trend) charts.trend.destroy();
    
    charts.trend = new Chart(ctx, {
      type: "line",
      data: { 
        labels, 
        datasets: [{ 
          label: "文章发布数", 
          data: values,
          borderColor: "#667eea",
          backgroundColor: "rgba(102, 126, 234, 0.1)",
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointHoverRadius: 8,
          pointBackgroundColor: "#667eea",
          pointBorderColor: "#fff",
          pointBorderWidth: 2
        }]
      },
      options: {
        ...chartDefaults,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false }
          },
          x: {
            ticks: { font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { display: false }
          }
        }
      }
    });
  } catch (error) {
    console.error('加载文章趋势失败:', error);
  }
}

// 分类分布饼图
async function loadCategoryChart() {
  try {
    const data = await fetchJSON("/dashboard/api/category_distribution/");
    const labels = data.map(r => r.name);
    const values = data.map(r => r.article_count);
    
    const ctx = document.getElementById("category-chart").getContext("2d");
    if (charts.category) charts.category.destroy();
    
    const colors = [
      'rgba(102, 126, 234, 0.8)', 'rgba(239, 68, 68, 0.8)',
      'rgba(16, 185, 129, 0.8)', 'rgba(245, 158, 11, 0.8)',
      'rgba(139, 92, 246, 0.8)', 'rgba(236, 72, 153, 0.8)',
      'rgba(6, 182, 212, 0.8)', 'rgba(132, 204, 22, 0.8)'
    ];
    
    charts.category = new Chart(ctx, {
      type: "doughnut",
      data: { 
        labels, 
        datasets: [{ 
          data: values,
          backgroundColor: colors,
          borderColor: '#fff',
          borderWidth: 3,
          hoverOffset: 15
        }]
      },
      options: {
        ...chartDefaults,
        cutout: '60%'
      }
    });
  } catch (error) {
    console.error('加载分类分布失败:', error);
  }
}

// 标签分布柱状图
async function loadTagChart() {
  try {
    const data = await fetchJSON("/dashboard/api/tag_distribution/?limit=10");
    const labels = data.map(r => r.name);
    const values = data.map(r => r.article_count);
    
    const ctx = document.getElementById("tag-chart").getContext("2d");
    if (charts.tag) charts.tag.destroy();
    
    charts.tag = new Chart(ctx, {
      type: "bar",
      data: { 
        labels, 
        datasets: [{ 
          label: "文章数", 
          data: values,
          backgroundColor: "rgba(16, 185, 129, 0.8)",
          borderColor: "#10b981",
          borderWidth: 2,
          borderRadius: 8
        }]
      },
      options: {
        ...chartDefaults,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false }
          },
          x: {
            ticks: { font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { display: false }
          }
        }
      }
    });
  } catch (error) {
    console.error('加载标签分布失败:', error);
  }
}

// ==================== 用户互动页面 ====================
// 点赞趋势图
async function loadLikeTrendChart(days = 7) {
  try {
    const data = await fetchJSON(`/dashboard/api/like_trend/?range=${days}`);
    const labels = data.map(r => r.day);
    const values = data.map(r => r.like_count);
    
    const ctx = document.getElementById("like-trend-chart").getContext("2d");
    if (charts.likeTrend) charts.likeTrend.destroy();
    
    charts.likeTrend = new Chart(ctx, {
      type: "line",
      data: { 
        labels, 
        datasets: [{ 
          label: "点赞数", 
          data: values,
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointHoverRadius: 8,
          pointBackgroundColor: "#ef4444",
          pointBorderColor: "#fff",
          pointBorderWidth: 2
        }]
      },
      options: {
        ...chartDefaults,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false }
          },
          x: {
            ticks: { font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { display: false }
          }
        }
      }
    });
  } catch (error) {
    console.error('加载点赞趋势失败:', error);
  }
}

// 收藏趋势图
async function loadFavoriteTrendChart(days = 7) {
  try {
    const data = await fetchJSON(`/dashboard/api/favorite_trend/?range=${days}`);
    const labels = data.map(r => r.day);
    const values = data.map(r => r.favorite_count);
    
    const ctx = document.getElementById("favorite-trend-chart").getContext("2d");
    if (charts.favoriteTrend) charts.favoriteTrend.destroy();
    
    charts.favoriteTrend = new Chart(ctx, {
      type: "line",
      data: { 
        labels, 
        datasets: [{ 
          label: "收藏数", 
          data: values,
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointHoverRadius: 8,
          pointBackgroundColor: "#f59e0b",
          pointBorderColor: "#fff",
          pointBorderWidth: 2
        }]
      },
      options: {
        ...chartDefaults,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false }
          },
          x: {
            ticks: { font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { display: false }
          }
        }
      }
    });
  } catch (error) {
    console.error('加载收藏趋势失败:', error);
  }
}

// 评论趋势图
async function loadCommentTrendChart(days = 7) {
  try {
    const data = await fetchJSON(`/dashboard/api/comment_trend/?range=${days}`);
    const labels = data.map(r => r.day);
    const values = data.map(r => r.comment_count);
    
    const ctx = document.getElementById("comment-trend-chart").getContext("2d");
    if (charts.commentTrend) charts.commentTrend.destroy();
    
    charts.commentTrend = new Chart(ctx, {
      type: "line",
      data: { 
        labels, 
        datasets: [{ 
          label: "评论数", 
          data: values,
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointHoverRadius: 8,
          pointBackgroundColor: "#10b981",
          pointBorderColor: "#fff",
          pointBorderWidth: 2
        }]
      },
      options: {
        ...chartDefaults,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false }
          },
          x: {
            ticks: { font: { size: 11, weight: '600' }, color: '#64748b' },
            grid: { display: false }
          }
        }
      }
    });
  } catch (error) {
    console.error('加载评论趋势失败:', error);
  }
}

// ==================== 用户统计页面 ====================
// 热门文章排行榜
async function loadTopArticles(limit = 10) {
  try {
    const data = await fetchJSON(`/dashboard/api/top/?limit=${limit}`);
    const tbody = document.querySelector("#top-articles-table tbody");
    tbody.innerHTML = "";
    
    data.forEach((row, idx) => {
      const tr = document.createElement("tr");
      const rankClass = idx === 0 ? 'top-1' : idx === 1 ? 'top-2' : idx === 2 ? 'top-3' : 'other';
      
      tr.innerHTML = `
        <td><span class="rank-badge ${rankClass}">${idx + 1}</span></td>
        <td><a href="/article/${row.id}/" target="_blank" style="color: #667eea; font-weight: 600; text-decoration: none;">${row.title}</a></td>
        <td><strong style="color: #8b5cf6;">${row.views.toLocaleString()}</strong></td>
        <td><strong style="color: #10b981;">${row.comment_count}</strong></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error('加载热门文章失败:', error);
  }
}

// 热门作者排行榜
async function loadTopAuthors(limit = 10) {
  try {
    const data = await fetchJSON(`/dashboard/api/top_authors/?limit=${limit}`);
    const tbody = document.querySelector("#top-authors-table tbody");
    tbody.innerHTML = "";
    
    data.forEach((row, idx) => {
      const tr = document.createElement("tr");
      const rankClass = idx === 0 ? 'top-1' : idx === 1 ? 'top-2' : idx === 2 ? 'top-3' : 'other';
      
      tr.innerHTML = `
        <td><span class="rank-badge ${rankClass}">${idx + 1}</span></td>
        <td><strong style="color: #2d3748;">${row.username}</strong></td>
        <td><strong style="color: #667eea;">${row.article_count}</strong></td>
        <td><strong style="color: #ef4444;">${row.total_views.toLocaleString()}</strong></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error('加载热门作者失败:', error);
  }
}

// ==================== 最近活动页面 ====================
async function loadActivities(limit = 20) {
  try {
    const data = await fetchJSON(`/dashboard/api/recent_activities/?limit=${limit}`);
    const timeline = document.getElementById("activity-timeline");
    timeline.innerHTML = "";
    
    const activityColors = {
      'article': '#667eea',
      'comment': '#10b981',
      'like': '#ef4444',
      'favorite': '#f59e0b'
    };
    
    const activityLabels = {
      'article': '发布文章',
      'comment': '发表评论',
      'like': '点赞',
      'favorite': '收藏'
    };
    
    data.forEach(activity => {
      const div = document.createElement("div");
      div.className = "activity-item";
      div.style.setProperty('--activity-color', activityColors[activity.type] || '#64748b');
      
      div.innerHTML = `
        <div>
          <span class="activity-badge" style="background: ${activityColors[activity.type]}; color: white;">
            ${activityLabels[activity.type] || activity.type}
          </span>
          <span class="activity-time">${activity.time}</span>
        </div>
        <div style="margin-top: 0.5rem; color: #475569;">
          ${activity.description}
        </div>
      `;
      timeline.appendChild(div);
    });
  } catch (error) {
    console.error('加载最近活动失败:', error);
  }
}
