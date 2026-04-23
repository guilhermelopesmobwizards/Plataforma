{% extends "endmonthapp/base.html" %}
{% load static %}

{% block title %}MAP Control — Campaigns{% endblock %}
{% block page_title %}Campaigns{% endblock %}
{% block nav_campaigns %}active{% endblock %}
{% block extra_head %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
{% endblock %}
{% block topbar_actions %}
<div class="filter-row">
                    <select class="filter-select">
                        <option>All Clients</option>
                        <option>Acme Corp</option>
                        <option>Beta Media</option>
                        <option>Gamma Ads</option>
                        <option>Delta Group</option>
                        <option>Epsilon Co</option>
                    </select>
                    <select class="filter-select">
                        <option>All Platforms</option>
                        <option>Google Ads</option>
                        <option>Meta Ads</option>
                        <option>TikTok</option>
                        <option>Others</option>
                    </select>
                    <select class="filter-select">
                        <option>All States</option>
                        <option>Active</option>
                        <option>Paused</option>
                        <option>Finished</option>
                    </select>
                    <button class="btn btn-ghost">
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                            <path d="M1 3h10M3 6h6M5 9h2" stroke="currentColor" stroke-width="1.5"
                                stroke-linecap="round" />
                        </svg>
                        Filter
                    </button>
                    <button class="btn btn-primary">
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                            <path d="M6 1v10M1 6h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                        </svg>
                        New Campaign
                    </button>
                </div>
{% endblock %}
{% block content %}


                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-label">Total Campaigns</div>
                        <div class="kpi-value accent">142</div>
                        <div class="kpi-delta delta-up">▲ 12 vs mês anterior</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Ativas</div>
                        <div class="kpi-value positive">98</div>
                        <div class="kpi-delta delta-up">▲ 5 esta semana</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Pausadas</div>
                        <div class="kpi-value">31</div>
                        <div class="kpi-delta delta-dn">▼ 3 esta semana</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Concluídas</div>
                        <div class="kpi-value">13</div>
                        <div class="kpi-sub">Este mês</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Taxa de Sucesso</div>
                        <div class="kpi-value positive">87.3%</div>
                        <div class="kpi-delta delta-up">▲ 2.1%</div>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-head">
                        <div>
                            <div class="panel-title">All Campaigns</div>
                            <div class="panel-sub">Apr 2025 — 142 campaigns</div>
                        </div>
                        <div style="display:flex;gap:8px;align-items:center;">
                            <input type="text" placeholder="Pesquisar campanha..."
                                style="background:var(--surface2);border:1px solid var(--border2);color:var(--text);font-family:var(--font-body);font-size:12px;padding:6px 10px;border-radius:var(--radius);outline:none;width:200px;">
                            <button class="btn btn-ghost" style="font-size:11px;">
                                <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                                    <path d="M1 2.5h9M3 5.5h5M4.5 8.5h2" stroke="currentColor" stroke-width="1.4"
                                        stroke-linecap="round" />
                                </svg>
                                Export
                            </button>
                        </div>
                    </div>
                    <div class="table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Client</th>
                                    <th>Country</th>
                                    <th>Platform</th>
                                    <th>Category</th>
                                    <th class="num">Custo EUR</th>
                                    <th class="num">Receita EUR</th>
                                    <th class="num">Margem</th>
                                    <th class="num">CPA</th>
                                    <th class="num">Conv.</th>
                                    <th class="num">ROI</th>
                                    <th>Início</th>
                                    <th>Fim</th>
                                    <th>Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><span class="chip"
                                            style="background:var(--surface2);color:var(--muted)">C-0001</span></td>
                                    <td>--Nome da Campanha--</td>
                                    <td>Acme Corp</td>
                                    <td><span class="tag tag-blue">PT</span></td>
                                    <td><span class="tag tag-blue">Google Ads</span></td>
                                    <td><span class="tag tag-purple">E-Commerce</span></td>
                                    <td class="num">€ 4 200</td>
                                    <td class="num">€ 14 700</td>
                                    <td class="num"><span style="color:var(--accent2)">68.2%</span></td>
                                    <td class="num">€ 2.10</td>
                                    <td class="num">2 000</td>
                                    <td class="num"><span style="color:var(--accent2)">3.50×</span></td>
                                    <td>01 Abr</td>
                                    <td>30 Abr</td>
                                    <td><span class="tag tag-green"><span
                                                class="status-dot dot-green"></span>Ativa</span></td>
                                </tr>
                                <tr>
                                    <td><span class="chip"
                                            style="background:var(--surface2);color:var(--muted)">C-0002</span></td>
                                    <td>--Nome da Campanha--</td>
                                    <td>Beta Media</td>
                                    <td><span class="tag tag-blue">ES</span></td>
                                    <td><span class="tag tag-amber">Meta Ads</span></td>
                                    <td><span class="tag tag-blue">Lead Gen</span></td>
                                    <td class="num">€ 6 800</td>
                                    <td class="num">€ 22 100</td>
                                    <td class="num"><span style="color:var(--accent2)">69.2%</span></td>
                                    <td class="num">€ 3.40</td>
                                    <td class="num">2 000</td>
                                    <td class="num"><span style="color:var(--accent2)">3.25×</span></td>
                                    <td>05 Abr</td>
                                    <td>30 Abr</td>
                                    <td><span class="tag tag-green"><span
                                                class="status-dot dot-green"></span>Ativa</span></td>
                                </tr>
                                <tr>
                                    <td><span class="chip"
                                            style="background:var(--surface2);color:var(--muted)">C-0003</span></td>
                                    <td>--Nome da Campanha--</td>
                                    <td>Gamma Ads</td>
                                    <td><span class="tag tag-blue">FR</span></td>
                                    <td><span class="tag tag-purple">TikTok</span></td>
                                    <td><span class="tag tag-amber">Marca</span></td>
                                    <td class="num">€ 3 100</td>
                                    <td class="num">€ 8 900</td>
                                    <td class="num"><span style="color:var(--warning)">65.2%</span></td>
                                    <td class="num">€ 5.17</td>
                                    <td class="num">600</td>
                                    <td class="num"><span style="color:var(--warning)">2.87×</span></td>
                                    <td>10 Abr</td>
                                    <td>25 Abr</td>
                                    <td><span class="tag tag-amber"><span
                                                class="status-dot dot-amber"></span>Pausada</span></td>
                                </tr>
                                <tr>
                                    <td><span class="chip"
                                            style="background:var(--surface2);color:var(--muted)">C-0004</span></td>
                                    <td>--Nome da Campanha--</td>
                                    <td>Delta Group</td>
                                    <td><span class="tag tag-blue">DE</span></td>
                                    <td><span class="tag tag-blue">Google Ads</span></td>
                                    <td><span class="tag tag-green">Retargeting</span></td>
                                    <td class="num">€ 8 500</td>
                                    <td class="num">€ 32 300</td>
                                    <td class="num"><span style="color:var(--accent2)">73.7%</span></td>
                                    <td class="num">€ 1.89</td>
                                    <td class="num">4 497</td>
                                    <td class="num"><span style="color:var(--accent2)">3.80×</span></td>
                                    <td>01 Abr</td>
                                    <td>30 Abr</td>
                                    <td><span class="tag tag-green"><span
                                                class="status-dot dot-green"></span>Ativa</span></td>
                                </tr>
                                <tr>
                                    <td><span class="chip"
                                            style="background:var(--surface2);color:var(--muted)">C-0005</span></td>
                                    <td>--Nome da Campanha--</td>
                                    <td>Epsilon Co</td>
                                    <td><span class="tag tag-blue">IT</span></td>
                                    <td><span class="tag tag-amber">Meta Ads</span></td>
                                    <td><span class="tag tag-purple">E-Commerce</span></td>
                                    <td class="num">€ 2 400</td>
                                    <td class="num">€ 5 100</td>
                                    <td class="num"><span style="color:var(--danger)">52.9%</span></td>
                                    <td class="num">€ 8.00</td>
                                    <td class="num">300</td>
                                    <td class="num"><span style="color:var(--danger)">2.13×</span></td>
                                    <td>15 Mar</td>
                                    <td>15 Abr</td>
                                    <td><span class="tag tag-gray"><span class="status-dot"
                                                style="background:var(--muted)"></span>Concluída</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div
                        style="display:flex;align-items:center;justify-content:space-between;padding:12px 20px;border-top:1px solid var(--border);font-size:11px;color:var(--muted);">
                        <span>A mostrar 1–12 de 142</span>
                        <div style="display:flex;gap:4px;">
                            <button class="btn btn-ghost" style="padding:4px 10px;font-size:11px;">← Anterior</button>
                            <button class="btn btn-ghost"
                                style="padding:4px 10px;font-size:11px;background:var(--surface2);color:var(--accent);">1</button>
                            <button class="btn btn-ghost" style="padding:4px 10px;font-size:11px;">2</button>
                            <button class="btn btn-ghost" style="padding:4px 10px;font-size:11px;">3</button>
                            <button class="btn btn-ghost" style="padding:4px 10px;font-size:11px;">Próximo →</button>
                        </div>
                    </div>
                </div>
{% endblock %}
