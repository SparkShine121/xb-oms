import request from './request'
const base = '/analytics'

/** 销售结算表：按业务员聚合 + 月度趋势（?year= &salesman=） */
export const getSalesSummary = (p?: any) =>
  request.get(`${base}/sales/`, { params: p })

/** 工厂账单汇总：应付/已付/未付（?year= &factory=） */
export const getFactorySummary = (p?: any) =>
  request.get(`${base}/factory-summary/`, { params: p })

/** 跟单信息汇总：节点分布 + 平均停留时长（?year=） */
export const getTrackingSummary = (p?: any) =>
  request.get(`${base}/tracking-summary/`, { params: p })

/** 年度总览：总额卡片 + 月度趋势（?year=） */
export const getOverview = (p?: any) =>
  request.get(`${base}/overview/`, { params: p })
