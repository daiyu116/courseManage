// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="license-page">
    <el-card class="license-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><Key /></el-icon> {{ t('license.title') }}</span>
          <el-button type="info" @click="goBack" size="small">
            <el-icon><ArrowLeft /></el-icon>
            {{ t('license.goBack') }}
          </el-button>
        </div>
      </template>

      <div v-if="licenseState.activated" class="license-status">
        <el-alert :title="t('license.activated')" type="success" :closable="false" show-icon />
        <el-alert type="success" :closable="false" show-icon style="margin-top:16px">
          <template #title>{{ t('license.defaultModulesTitle') }}</template>
          <div class="default-modules-grid">
            <span v-for="mod in defaultModules" :key="mod" class="default-module-tag">
              <el-icon><CircleCheck /></el-icon> {{ mod }}
            </span>
          </div>
        </el-alert>
        <el-descriptions :column="2" border size="small" style="margin-top:12px">
          <el-descriptions-item :label="t('license.organization')">{{ licenseState.organizationName || '--' }}</el-descriptions-item>
          <el-descriptions-item :label="t('license.licenseType')">{{ licenseState.licenseTypeName || '--' }}</el-descriptions-item>
          <el-descriptions-item label="License Key">
            <span>{{ licenseState.licenseKey ? licenseState.licenseKey.substring(0, 20) + '...' : '--' }}</span>
            <el-button v-if="licenseState.licenseKey" type="primary" link size="small" @click="copyText(licenseState.licenseKey)">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </el-descriptions-item>
          <el-descriptions-item :label="t('license.machineCode')">
            <span>{{ licenseState.machineCode || '--' }}</span>
            <el-button v-if="licenseState.machineCode" type="primary" link size="small" @click="copyText(licenseState.machineCode)">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </el-descriptions-item>
          <el-descriptions-item :label="t('license.licenseIssuedAt')">{{ licenseState.issuedAt ? formatDateTime(licenseState.issuedAt) : '--' }}</el-descriptions-item>
          <el-descriptions-item :label="t('license.validity')">{{ licenseState.expiryDate ? formatDateTime(licenseState.expiryDate) : t('license.permanent') }}</el-descriptions-item>
          <el-descriptions-item :label="t('license.thirdPartyDiscount')">{{ licenseState.discountPercent != null ? licenseState.discountPercent + '%' : '--' }}</el-descriptions-item>
          <el-descriptions-item :label="t('license.referrerReward')">{{ licenseState.rebatePercent != null ? licenseState.rebatePercent + '%' : '--' }}</el-descriptions-item>
          <el-descriptions-item :label="t('license.authorizedAdvancedFeatures')" :span="2">
            <el-tag v-for="(enabled, key) in licenseState.features" :key="key" :type="enabled ? 'success' : 'info'" size="small" style="margin:2px">{{ FEATURE_NAMES[key] ? t(FEATURE_NAMES[key]) : key }}</el-tag>
            <span v-if="!Object.keys(licenseState.features).length">--</span>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="licenseState.referralCode" class="referral-code-box">
          <div class="referral-code-main">
            <el-tag :type="licenseState.referralActivated ? 'success' : 'warning'" size="large" effect="plain" style="font-size:14px;padding:6px 14px">
              <el-icon><Tickets /></el-icon>
              {{ t('license.yourReferralCode') }}<strong style="font-size:16px;letter-spacing:2px">{{ licenseState.referralCode }}</strong>
              <span v-if="licenseState.discountPercent != null" style="margin-left:8px;font-size:12px;color:#409eff">{{ t('license.thirdPartyDiscount') }}{{ licenseState.discountPercent }}%</span>
              <span v-if="licenseState.rebatePercent != null" style="margin-left:8px;font-size:12px;color:#67c23a">{{ t('license.referrerReward') }}{{ licenseState.rebatePercent }}%</span>
            </el-tag>
            <el-button v-if="licenseState.referralActivated" size="small" @click="copyText(licenseState.referralCode)" style="margin-left:8px">
              <el-icon><CopyDocument /></el-icon> {{ t('license.copy') }}
            </el-button>
          </div>
          <div v-if="licenseState.referralActivated" class="referral-code-hint" style="color:#67c23a">
            {{ t('license.referralActivated', { percent: licenseState.rebatePercent }) }}
          </div>
          <div v-else class="referral-code-hint" style="color:#E6A23C">
            {{ t('license.referralNotActivated') }}
            {{ t('license.referralPending', { total: licenseState.totalSpending.toFixed(2), threshold: licenseState.referralThreshold.toFixed(2), remaining: Math.max(0, licenseState.referralThreshold - licenseState.totalSpending).toFixed(2) }) }}
            <el-progress
              :percentage="Math.min(100, licenseState.referralThreshold > 0 ? (licenseState.totalSpending / licenseState.referralThreshold * 100) : 0)"
              :stroke-width="8"
              :format="() => Math.min(100, licenseState.referralThreshold > 0 ? Math.round(licenseState.totalSpending / licenseState.referralThreshold * 100) : 0) + '%'"
              style="margin-top:6px;max-width:300px"
            />
          </div>
        </div>
        <el-divider />
        <h4>{{ t('license.authorizedModules') }}</h4>
        <el-row :gutter="12">
          <el-col :xs="12" :sm="8" :md="8" v-for="feat in featureList" :key="feat.key">
            <el-tooltip effect="dark" placement="top" :show-after="300">
              <template #content>
                <div style="max-width: 320px;">
                  <div style="font-weight: bold; font-size: 14px; margin-bottom: 6px;">{{ t(feat.name) }}</div>
                  <div v-if="FEATURE_DESCRIPTIONS[feat.key]" style="margin-bottom: 4px;">
                    <span style="color: #67c23a;">✦ {{ t(FEATURE_DESCRIPTIONS[feat.key].highlights) }}</span>
                  </div>
                  <div v-if="FEATURE_DESCRIPTIONS[feat.key]" style="color: #c0c4cc; line-height: 1.6; white-space: pre-line;">{{ t(FEATURE_DESCRIPTIONS[feat.key].details) }}</div>
                </div>
              </template>
              <el-card
                :class="['feature-card', feat.enabled ? 'enabled' : 'disabled']"
                shadow="hover"
              >
                <el-icon :size="24"><component :is="feat.icon" /></el-icon>
                <span>{{ t(feat.name) }}</span>
                <el-tooltip v-if="feat.enabled" effect="dark" placement="top">
                  <template #content>
                    <div>{{ t('license.organization') }}: {{ licenseState.organizationName || '--' }}</div>
                    <div>{{ t('license.licenseType') }}: {{ licenseState.licenseTypeName || '--' }}</div>
                    <div v-if="licenseState.expiryDate">{{ t('license.expiryDate') }}: {{ formatDateTime(licenseState.expiryDate) }}</div>
                    <div v-else>{{ t('license.validity') }}: {{ t('license.permanent') }}</div>
                  </template>
                  <el-tag type="success" size="small" style="cursor:default">{{ t('license.authorized') }}</el-tag>
                </el-tooltip>
                <el-tag v-else type="info" size="small">{{ t('license.unauthorized') }}</el-tag>
                <div v-if="feat.enabled" style="display: flex; gap: 6px; margin-top: 4px;">
                  <el-button
                    type="primary"
                    size="small"
                    plain
                    @click="openFeatureFeedbackDialog(feat)"
                  >
                    <el-icon><ChatLineSquare /></el-icon> {{ t('license.feedback') }}
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    plain
                    :loading="featureDeactivating === feat.key"
                    @click="handleDeactivateFeature(feat)"
                  >
                    {{ t('license.deactivate') }}
                  </el-button>
                </div>
              </el-card>
            </el-tooltip>
          </el-col>
        </el-row>
        <el-divider />
        <el-collapse v-model="activeCollapse">
          <el-collapse-item name="addon">
            <template #title>
              <el-button class="addon-title-btn" type="warning" size="default" round>
                <el-icon><Plus /></el-icon> {{ t('license.addonLicense') }}
              </el-button>
            </template>
            <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px">
              <template #title>{{ t('license.licenseFlow') }}</template>
              <p>{{ t('license.licenseFlowDesc') }}</p>
            </el-alert>
            <div class="steps-container">
              <div class="step-card">
                <div class="step-header">
                  <span class="step-number">1</span>
                  <span class="step-title">{{ t('license.step1SelectModule') }}</span>
                </div>
                <div class="step-body">
                  <el-alert
                    v-if="addonFeatureOptions.length === 0"
                    type="success"
                    :closable="false"
                    show-icon
                  >
                    <template #title>{{ t('license.allModulesAuthorized') }}</template>
                    {{ t('license.allModulesAuthorizedDesc') }}
                  </el-alert>
                  <el-row :gutter="12" v-else>
                    <el-col :xs="12" :sm="8" :md="8" v-for="opt in addonFeatureOptions" :key="opt.key">
                      <el-tooltip effect="dark" placement="top" :show-after="300">
                        <template #content>
                          <div style="max-width: 320px;">
                            <div style="font-weight: bold; font-size: 14px; margin-bottom: 6px;">{{ t(opt.name) }}</div>
                            <div v-if="FEATURE_DESCRIPTIONS[opt.key]" style="margin-bottom: 4px;">
                              <span style="color: #67c23a;">✦ {{ t(FEATURE_DESCRIPTIONS[opt.key].highlights) }}</span>
                            </div>
                            <div v-if="FEATURE_DESCRIPTIONS[opt.key]" style="color: #c0c4cc; line-height: 1.6; white-space: pre-line;">{{ t(FEATURE_DESCRIPTIONS[opt.key].details) }}</div>
                          </div>
                        </template>
                        <el-card
                          :class="['feature-card', 'selectable', addonSelectedFeatures.includes(opt.key) ? 'selected' : '']"
                          shadow="hover"
                          @click="toggleAddonFeature(opt.key)"
                        >
                          <el-icon :size="24"><component :is="opt.icon" /></el-icon>
                          <span>{{ t(opt.name) }}</span>
                          <el-tag v-if="addonSelectedFeatures.includes(opt.key)" type="success" size="small">{{ t('license.selected') }}</el-tag>
                          <el-tag v-else type="info" size="small">{{ t('license.clickToSelect') }}</el-tag>
                        </el-card>
                      </el-tooltip>
                    </el-col>
                  </el-row>
                </div>
              </div>

              <div class="step-arrow">
                <el-icon :size="24"><ArrowRight /></el-icon>
              </div>

              <div class="step-card step-card-wide">
                <div class="step-header">
                  <span class="step-number">2</span>
                  <span class="step-title">{{ t('license.step2ApplyLicense') }}</span>
                </div>
                <div class="step-body">
                  <el-form label-position="top">
                    <el-form-item :label="t('license.machineCodeLabel')">
                      <el-input v-model="machineCode" readonly size="small">
                        <template #append>
                          <el-button @click="copyMachineCode" size="small">
                            <el-icon><CopyDocument /></el-icon>
                          </el-button>
                        </template>
                      </el-input>
                    </el-form-item>
                    <el-form-item :label="t('license.licenseTypeLabel')">
                      <el-radio-group v-model="addonLicenseType" style="line-height:32px">
                        <el-radio v-for="(info, key) in LICENSE_TYPES" :key="key" :value="key" border size="small" style="margin-right:8px;margin-bottom:6px">
                          {{ t(info.name) }}{{ info.days ? ' (' + t('license.daysType', { n: info.days }) + ')' : ' (' + t('license.permanentType') + ')' }}
                        </el-radio>
                      </el-radio-group>
                      <div v-if="addonLicenseType && addonSelectedFeatures.length" style="margin-top:8px;padding:8px 12px;background:#f0f9eb;border-radius:4px;border:1px solid #e1f3d8">
                        <div style="font-size:13px;color:#606266;margin-bottom:4px">{{ t('license.costDetail', { name: t(LICENSE_TYPES[addonLicenseType].name), period: LICENSE_TYPES[addonLicenseType].days ? ' / ' + t('license.daysType', { n: LICENSE_TYPES[addonLicenseType].days }) : ' / ' + t('license.permanentType') }) }}</div>
                        <div v-for="feat in addonSelectedFeatures" :key="feat" style="display:flex;justify-content:space-between;font-size:12px;color:#909399;padding:2px 0">
                          <span>{{ FEATURE_NAMES[feat] ? t(FEATURE_NAMES[feat]) : feat }}</span>
                          <span style="color:#409eff;font-weight:500">¥{{ (FEATURE_PRICES[feat] && FEATURE_PRICES[feat][addonLicenseType]) || 0 }}</span>
                        </div>
                        <el-divider style="margin:6px 0" />
                        <div style="display:flex;justify-content:space-between;font-size:14px;font-weight:600">
                          <span>{{ t('license.total') }}</span>
                          <span style="color:#E6A23C">¥{{ calcTotalPrice(addonSelectedFeatures, addonLicenseType) }}</span>
                        </div>
                      </div>
                    </el-form-item>
                    <el-alert type="warning" :closable="false" show-icon style="margin-bottom:12px">
                      {{ t('license.contactInfoRequired') }}
                    </el-alert>
                    <el-form-item :label="t('license.orgNameLabel')" required>
                      <el-input v-model="orgName" :placeholder="t('license.orgNamePlaceholder')" />
                    </el-form-item>
                    <el-form-item :label="t('license.contactPersonLabel')" required>
                      <el-input v-model="contactPerson" :placeholder="t('license.contactPersonPlaceholder')" />
                    </el-form-item>
                    <el-form-item :label="t('license.contactPhoneLabel')">
                      <el-input v-model="contactPhone" :placeholder="t('license.contactPhonePlaceholder')" />
                    </el-form-item>
                    <el-form-item :label="t('license.contactEmailLabel')">
                      <el-input v-model="contactEmail" :placeholder="t('license.contactEmailPlaceholder')" />
                    </el-form-item>
                    <el-form-item :label="t('license.contactWechatLabel')">
                      <el-input v-model="contactWechat" :placeholder="t('license.contactWechatPlaceholder')" />
                    </el-form-item>
                    <el-form-item :label="t('license.remarksLabel')">
                      <el-input v-model="remarks" type="textarea" :rows="2" :placeholder="t('license.remarksPlaceholder')" />
                    </el-form-item>
                    <el-form-item :label="t('license.referralCodeLabel')">
                      <el-input v-model="addonReferralCode" :placeholder="t('license.referralCodePlaceholder')" clearable>
                        <template #prefix>
                          <el-icon><Tickets /></el-icon>
                        </template>
                      </el-input>
                      <div v-if="licenseState.referralCode" style="font-size:12px;color:#E6A23C;margin-top:4px">
                        {{ t('license.ownReferralCodeWarning', { code: licenseState.referralCode }) }}
                      </div>
                    </el-form-item>
                    <el-form-item>
                      <el-button
                        type="warning"
                        size="default"
                        @click="handleApplyAddon"
                        :loading="addonApplying"
                        :disabled="!addonSelectedFeatures.length || !addonLicenseType || !orgName || !contactPerson || (!contactPhone && !contactEmail && !contactWechat) || isOwnReferralCode(addonReferralCode)"
                      >
                        <el-icon><Message /></el-icon> {{ t('license.applyAddonLicense') }}
                      </el-button>
                    </el-form-item>
                  </el-form>
                </div>
              </div>

              <div class="step-arrow">
                <el-icon :size="24"><ArrowRight /></el-icon>
              </div>

              <div class="step-card">
                <div class="step-header">
                  <span class="step-number">3</span>
                  <span class="step-title">{{ t('license.step3Purchase') }}</span>
                </div>
                <div class="step-body">
                  <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px">
                    <template #title>{{ t('license.purchaseNote') }}</template>
                    {{ t('license.purchaseNoteDetail') }}
                  </el-alert>
                  <div v-if="!showAddonSupplierInfo" class="supplier-mask-wrapper">
                    <div class="supplier-mask-overlay">
                      <div class="supplier-mask-content">
                        <el-icon :size="32" color="#909399"><Lock /></el-icon>
                        <p style="color:#606266;margin:8px 0;font-size:14px">{{ t('license.supplierInfoHidden') }}</p>
                        <el-input v-model="inputAddonMachineCode" :placeholder="t('license.inputMachineCodePlaceholder')" @keyup.enter="verifyAddonMachineCode" style="max-width:360px" />
                        <el-button type="primary" @click="verifyAddonMachineCode" style="margin-top:8px">{{ t('license.verifyMachineCode') }}</el-button>
                      </div>
                    </div>
                  </div>
                  <el-descriptions v-else :column="1" border size="small">
                    <el-descriptions-item :label="t('license.supplierEmail')">meitianqiusuo@163.com</el-descriptions-item>
                    <el-descriptions-item :label="t('license.supplierWechat')">renshengxiubuqi</el-descriptions-item>
                    <el-descriptions-item :label="t('license.supplierPhone')">+86-155-5418-6956</el-descriptions-item>
                  </el-descriptions>
                  <p style="color:#909399;font-size:12px;margin-top:8px">{{ t('license.nextStepHint') }}</p>
                </div>
              </div>

              <div class="step-arrow">
                <el-icon :size="24"><ArrowRight /></el-icon>
              </div>

              <div class="step-card">
                <div class="step-header">
                  <span class="step-number">4</span>
                  <span class="step-title">{{ t('license.step4Activate') }}</span>
                </div>
                <div class="step-body">
                  <p style="color:#909399;margin-bottom:12px">{{ t('license.activateHint') }}</p>
                  <el-form label-position="top">
                    <el-form-item label="License Key">
                      <el-input
                        v-model="addonLicenseKey"
                        type="textarea"
                        :rows="3"
                        :placeholder="t('license.licenseKeyPlaceholder')"
                      />
                    </el-form-item>
                    <el-form-item>
                      <el-button
                        type="success"
                        size="default"
                        @click="handleAddonActivate"
                        :loading="addonActivating"
                        :disabled="!addonLicenseKey.trim() || !addonSelectedFeatures.length"
                      >
                        <el-icon><Check /></el-icon> {{ t('license.addonLicense') }}
                      </el-button>
                    </el-form-item>
                  </el-form>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
        <el-divider />
        <div style="display: flex; gap: 12px;">
          <el-button type="danger" @click="handleDeactivate" :loading="deactivating">
            {{ t('license.deactivateLicense') }}
          </el-button>
          <el-button type="primary" plain @click="openSystemFeedbackDialog">
            <el-icon><ChatLineSquare /></el-icon> {{ t('license.systemFeedback') }}
          </el-button>
        </div>
        <el-collapse v-if="licenseState.deactivatedLicenses.length" v-model="deactivatedCollapse" style="margin-top:16px">
          <el-collapse-item name="history">
            <template #title>
              <span style="font-weight:bold;color:#E6A23C">
                <el-icon><Warning /></el-icon> {{ t('license.deactivatedLicenses', { filtered: filteredDeactivatedLicenses.length, total: licenseState.deactivatedLicenses.length }) }}
              </span>
            </template>
            <div class="deactivated-filter-bar">
              <el-radio-group v-model="deactivatedStatusFilter" size="small">
                <el-radio-button value="unexpired">{{ t('license.unexpired') }}</el-radio-button>
                <el-radio-button value="expired">{{ t('license.expired') }}</el-radio-button>
                <el-radio-button value="all">{{ t('license.all') }}</el-radio-button>
              </el-radio-group>
              <el-input
                v-model="deactivatedSearchKeyword"
                :placeholder="t('license.searchPlaceholder')"
                clearable
                size="small"
                style="max-width:280px;margin-left:12px"
              >
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </div>
            <el-table :data="filteredDeactivatedLicenses" border size="small" style="width:100%;margin-top:8px">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="license_key" label="License Key" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span>{{ row.license_key ? row.license_key.substring(0, 20) + '...' : '--' }}</span>
                  <el-button v-if="row.license_key && !isLicenseExpired(row)" type="primary" link size="small" @click="copyText(row.license_key)">
                    <el-icon><CopyDocument /></el-icon>
                  </el-button>
                  <el-tag v-if="isLicenseExpired(row)" type="danger" size="small">{{ t('license.expired') }}</el-tag>
                  <el-tooltip v-if="!isLicenseExpired(row) && isMachineCodeChanged(row)" :content="t('license.machineCodeChangedTip')" placement="top">
                    <el-tag type="warning" size="small" style="margin-left:4px">{{ t('license.machineCodeChanged') }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="organization_name" :label="t('license.organization')" min-width="120" show-overflow-tooltip>
                <template #default="{ row }">{{ row.organization_name || '--' }}</template>
              </el-table-column>
              <el-table-column prop="license_type_name" :label="t('license.licenseType')" min-width="100" show-overflow-tooltip>
                <template #default="{ row }">{{ row.license_type_name || '--' }}</template>
              </el-table-column>
              <el-table-column :label="t('license.licenseIssuedAt')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.issued_at">{{ formatDateTime(row.issued_at) }}</span>
                  <span v-else>--</span>
                </template>
              </el-table-column>
              <el-table-column :label="t('license.appliedFeatures')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <template v-if="row.feature_names && row.feature_names.length">
                    <el-tag v-for="fn in row.feature_names" :key="fn" size="small" style="margin:2px">{{ fn }}</el-tag>
                  </template>
                  <template v-else-if="row.features && row.features.length">
                    <el-tag v-for="f in row.features" :key="f" size="small" style="margin:2px">{{ FEATURE_NAMES[f] ? t(FEATURE_NAMES[f]) : f }}</el-tag>
                  </template>
                  <span v-else>--</span>
                </template>
              </el-table-column>
              <el-table-column :label="t('license.validity')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.expiry_date">{{ formatDateTime(row.expiry_date) }}</span>
                  <span v-else>{{ t('license.permanent') }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="machine_code" :label="t('license.machineCode')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <span>{{ row.machine_code || '--' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="deactivated_at" :label="t('license.deactivatedAt')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">{{ formatDateTime(row.deactivated_at) }}</template>
              </el-table-column>
              <el-table-column :label="t('common.operation')" min-width="140" fixed="right">
                <template #default="{ row }">
                  <el-button
                    v-if="!isLicenseExpired(row) && isMachineCodeChanged(row)"
                    type="warning"
                    size="small"
                    plain
                    :loading="replaceLicenseLoading === row.license_key"
                    @click="handleRequestReplaceLicense(row)"
                  >
                    {{ t('license.requestReplace') }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
        <el-divider />
      </div>

      <div v-else class="license-activate">
        <div v-if="licenseState.referralCode" class="referral-code-box" style="margin-top:16px">
          <div class="referral-code-main">
            <el-tag :type="licenseState.referralActivated ? 'success' : 'warning'" size="large" effect="plain" style="font-size:14px;padding:6px 14px">
              <el-icon><Tickets /></el-icon>
              {{ t('license.yourReferralCode') }}<strong style="font-size:16px;letter-spacing:2px">{{ licenseState.referralCode }}</strong>
              <span v-if="licenseState.discountPercent != null" style="margin-left:8px;font-size:12px;color:#409eff">{{ t('license.thirdPartyDiscount') }}{{ licenseState.discountPercent }}%</span>
              <span v-if="licenseState.rebatePercent != null" style="margin-left:8px;font-size:12px;color:#67c23a">{{ t('license.referrerReward') }}{{ licenseState.rebatePercent }}%</span>
            </el-tag>
            <el-button v-if="licenseState.referralActivated" size="small" @click="copyText(licenseState.referralCode)" style="margin-left:8px">
              <el-icon><CopyDocument /></el-icon> {{ t('license.copy') }}
            </el-button>
          </div>
          <div v-if="licenseState.referralActivated" class="referral-code-hint" style="color:#67c23a">
            {{ t('license.referralActivated', { percent: licenseState.rebatePercent }) }}
          </div>
          <div v-else class="referral-code-hint" style="color:#E6A23C">
            {{ t('license.referralNotActivated') }}
            {{ t('license.referralPending', { total: licenseState.totalSpending.toFixed(2), threshold: licenseState.referralThreshold.toFixed(2), remaining: Math.max(0, licenseState.referralThreshold - licenseState.totalSpending).toFixed(2) }) }}
            <el-progress
              :percentage="Math.min(100, licenseState.referralThreshold > 0 ? (licenseState.totalSpending / licenseState.referralThreshold * 100) : 0)"
              :stroke-width="8"
              :format="() => Math.min(100, licenseState.referralThreshold > 0 ? Math.round(licenseState.totalSpending / licenseState.referralThreshold * 100) : 0) + '%'"
              style="margin-top:6px;max-width:300px"
            />
          </div>
        </div>
        <el-alert type="success" :closable="false" show-icon style="margin-top:16px">
          <template #title>{{ t('license.defaultModulesTitle') }}</template>
          <div class="default-modules-grid">
            <span v-for="mod in defaultModules" :key="mod" class="default-module-tag">
              <el-icon><CircleCheck /></el-icon> {{ mod }}
            </span>
          </div>
        </el-alert>
        <el-alert :title="t('license.advancedNotAuthorized')" type="warning" :closable="false" show-icon style="margin-bottom:16px">
          <template #default>
            <p>{{ t('license.advancedNotAuthorizedDesc') }}</p>
          </template>
        </el-alert>
        <el-alert type="info" :closable="false" show-icon style="margin-bottom:16px">
          <template #title>{{ t('license.licenseFlow') }}</template>
          <p>{{ t('license.licenseFlowDesc') }}</p>
        </el-alert>

        <div class="steps-container">
          <div class="step-card">
            <div class="step-header">
              <span class="step-number">1</span>
              <span class="step-title">{{ t('license.step1SelectModule') }}</span>
            </div>
            <div class="step-body">
              <el-row :gutter="12">
                <el-col :xs="12" :sm="8" :md="8" v-for="opt in allFeatureOptions" :key="opt.key">
                  <el-tooltip effect="dark" placement="top" :show-after="300">
                    <template #content>
                      <div style="max-width: 320px;">
                        <div style="font-weight: bold; font-size: 14px; margin-bottom: 6px;">{{ t(opt.name) }}</div>
                        <div v-if="FEATURE_DESCRIPTIONS[opt.key]" style="margin-bottom: 4px;">
                          <span style="color: #67c23a;">✦ {{ t(FEATURE_DESCRIPTIONS[opt.key].highlights) }}</span>
                        </div>
                        <div v-if="FEATURE_DESCRIPTIONS[opt.key]" style="color: #c0c4cc; line-height: 1.6; white-space: pre-line;">{{ t(FEATURE_DESCRIPTIONS[opt.key].details) }}</div>
                      </div>
                    </template>
                    <el-card
                      :class="['feature-card', 'selectable', selectedFeatures.includes(opt.key) ? 'selected' : '']"
                      shadow="hover"
                      @click="toggleFeature(opt.key)"
                    >
                      <el-icon :size="24"><component :is="opt.icon" /></el-icon>
                      <span>{{ t(opt.name) }}</span>
                      <el-tag v-if="selectedFeatures.includes(opt.key)" type="success" size="small">{{ t('license.selected') }}</el-tag>
                      <el-tag v-else type="info" size="small">{{ t('license.clickToSelect') }}</el-tag>
                    </el-card>
                  </el-tooltip>
                </el-col>
              </el-row>
            </div>
          </div>

          <div class="step-arrow">
            <el-icon :size="24"><ArrowRight /></el-icon>
          </div>

          <div class="step-card step-card-wide">
            <div class="step-header">
              <span class="step-number">2</span>
              <span class="step-title">{{ t('license.step2ApplyLicense') }}</span>
            </div>
            <div class="step-body">
              <el-form label-width="100px" label-position="top">
                <el-form-item :label="t('license.machineCodeLabel')">
                  <el-input v-model="machineCode" readonly>
                    <template #append>
                      <el-button @click="copyMachineCode">
                        <el-icon><CopyDocument /></el-icon> {{ t('license.copy') }}
                      </el-button>
                    </template>
                  </el-input>
                </el-form-item>
                <el-form-item :label="t('license.licenseTypeLabel')">
                  <el-radio-group v-model="selectedLicenseType" style="line-height:32px">
                    <el-radio v-for="(info, key) in LICENSE_TYPES" :key="key" :value="key" border size="small" style="margin-right:8px;margin-bottom:6px">
                      {{ t(info.name) }}{{ info.days ? ' (' + t('license.daysType', { n: info.days }) + ')' : ' (' + t('license.permanentType') + ')' }}
                    </el-radio>
                  </el-radio-group>
                  <div v-if="selectedLicenseType && selectedFeatures.length" style="margin-top:8px;padding:8px 12px;background:#f0f9eb;border-radius:4px;border:1px solid #e1f3d8">
                    <div style="font-size:13px;color:#606266;margin-bottom:4px">{{ t('license.costDetail', { name: t(LICENSE_TYPES[selectedLicenseType].name), period: LICENSE_TYPES[selectedLicenseType].days ? ' / ' + t('license.daysType', { n: LICENSE_TYPES[selectedLicenseType].days }) : ' / ' + t('license.permanentType') }) }}：</div>
                    <div style="font-size:13px;color:#606266;margin-bottom:4px">{{ t('license.costNoteCny') }}</div>
                    <div v-for="feat in selectedFeatures" :key="feat" style="display:flex;justify-content:space-between;font-size:12px;color:#909399;padding:2px 0">
                      <span>{{ FEATURE_NAMES[feat] ? t(FEATURE_NAMES[feat]) : feat }}</span>
                      <span style="color:#409eff;font-weight:500">¥{{ (FEATURE_PRICES[feat] && FEATURE_PRICES[feat][selectedLicenseType]) || 0 }}</span>
                    </div>
                    <el-divider style="margin:6px 0" />
                    <div style="display:flex;justify-content:space-between;font-size:14px;font-weight:600">
                      <span>{{ t('license.total') }}</span>
                      <span style="color:#E6A23C">¥{{ calcTotalPrice(selectedFeatures, selectedLicenseType) }}</span>
                    </div>
                  </div>
                </el-form-item>
                <el-alert type="warning" :closable="false" show-icon style="margin-bottom:12px">
                  {{ t('license.contactInfoRequiredShort') }}
                </el-alert>
                <el-form-item :label="t('license.orgNameLabel')" required>
                  <el-input v-model="orgName" :placeholder="t('license.orgNamePlaceholder')" />
                </el-form-item>
                <el-form-item :label="t('license.contactPersonLabel')" required>
                  <el-input v-model="contactPerson" :placeholder="t('license.contactPersonPlaceholder')" />
                </el-form-item>
                <el-form-item :label="t('license.contactPhoneLabel')">
                  <el-input v-model="contactPhone" :placeholder="t('license.contactPhonePlaceholder')" />
                </el-form-item>
                <el-form-item :label="t('license.contactEmailLabel')">
                  <el-input v-model="contactEmail" :placeholder="t('license.contactPhonePlaceholder')" />
                </el-form-item>
                <el-form-item :label="t('license.contactWechatLabel')">
                  <el-input v-model="contactWechat" :placeholder="t('license.contactPhonePlaceholder')" />
                </el-form-item>
                <el-form-item :label="t('license.remarksLabel')">
                  <el-input v-model="remarks" type="textarea" :rows="2" :placeholder="t('license.remarksPlaceholder')" />
                </el-form-item>
                <el-form-item :label="t('license.referralCodeLabel')">
                  <el-input v-model="applyReferralCode" :placeholder="t('license.referralCodePlaceholder')" clearable>
                    <template #prefix>
                      <el-icon><Tickets /></el-icon>
                    </template>
                  </el-input>
                  <div v-if="licenseState.referralCode" style="font-size:12px;color:#E6A23C;margin-top:4px">
                    {{ t('license.ownReferralCodeWarning2', { code: licenseState.referralCode }) }}
                  </div>
                </el-form-item>
                <el-form-item>
                  <el-button
                    type="warning"
                    size="large"
                    @click="handleApplyLicense"
                    :loading="applyingLicense"
                    :disabled="!selectedFeatures.length || !selectedLicenseType || !orgName || !contactPerson || (!contactPhone && !contactEmail && !contactWechat) || isOwnReferralCode(applyReferralCode)"
                  >
                    <el-icon><Message /></el-icon> {{ t('license.applyLicense') }}
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>

          <div class="step-arrow">
            <el-icon :size="24"><ArrowRight /></el-icon>
          </div>

          <div class="step-card">
            <div class="step-header">
              <span class="step-number">3</span>
              <span class="step-title">{{ t('license.step3Purchase') }}</span>
            </div>
            <div class="step-body">
              <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px">
                <template #title>{{ t('license.purchaseNote') }}</template>
                {{ t('license.purchaseNoteDetailShort') }}
              </el-alert>
              <div v-if="!showSupplierInfo" class="supplier-mask-wrapper">
                <div class="supplier-mask-overlay">
                  <div class="supplier-mask-content">
                    <el-icon :size="32" color="#909399"><Lock /></el-icon>
                    <p style="color:#606266;margin:8px 0;font-size:14px">{{ t('license.supplierInfoHidden') }}</p>
                    <el-input v-model="inputMachineCode" :placeholder="t('license.inputMachineCodePlaceholder')" @keyup.enter="verifyMachineCode" style="max-width:360px" />
                    <el-button type="primary" @click="verifyMachineCode" style="margin-top:8px">{{ t('license.verifyMachineCode') }}</el-button>
                  </div>
                </div>
              </div>
              <el-descriptions v-else :column="1" border size="small">
                <el-descriptions-item :label="t('license.supplierEmail')">meitianqiusuo@163.com</el-descriptions-item>
                <el-descriptions-item :label="t('license.supplierWechat')">renshengxiubuqi</el-descriptions-item>
                <el-descriptions-item :label="t('license.supplierPhone')">+86-155-5418-6956</el-descriptions-item>
              </el-descriptions>
              <p style="color:#909399;font-size:12px;margin-top:8px">{{ t('license.nextStepHintShort') }}</p>
            </div>
          </div>

          <div class="step-arrow">
            <el-icon :size="24"><ArrowRight /></el-icon>
          </div>

          <div class="step-card">
            <div class="step-header">
              <span class="step-number">4</span>
              <span class="step-title">{{ t('license.step4Activate') }}</span>
            </div>
            <div class="step-body">
              <p style="color:#909399;margin-bottom:12px">{{ t('license.activateHint') }}</p>
              <el-form label-position="top">
                <el-form-item label="License Key">
                  <el-input
                    v-model="licenseKeyInput"
                    type="textarea"
                    :rows="3"
                    :placeholder="t('license.licenseKeyPlaceholderNew')"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button
                    type="primary"
                    size="large"
                    @click="handleActivate"
                    :loading="activating"
                    :disabled="!licenseKeyInput.trim()"
                  >
                    <el-icon><Check /></el-icon> {{ t('license.step4Activate') }}
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>
        <el-divider />
        <el-collapse v-if="licenseState.deactivatedLicenses.length" v-model="deactivatedCollapse" style="margin-top:16px">
          <el-collapse-item name="history">
            <template #title>
              <span style="font-weight:bold;color:#E6A23C">
                <el-icon><Warning /></el-icon> {{ t('license.deactivatedLicenses', { filtered: filteredDeactivatedLicenses.length, total: licenseState.deactivatedLicenses.length }) }}
              </span>
            </template>
            <div class="deactivated-filter-bar">
              <el-radio-group v-model="deactivatedStatusFilter" size="small">
                <el-radio-button value="unexpired">{{ t('license.unexpired') }}</el-radio-button>
                <el-radio-button value="expired">{{ t('license.expired') }}</el-radio-button>
                <el-radio-button value="all">{{ t('license.all') }}</el-radio-button>
              </el-radio-group>
              <el-input
                v-model="deactivatedSearchKeyword"
                :placeholder="t('license.searchPlaceholder')"
                clearable
                size="small"
                style="max-width:280px;margin-left:12px"
              >
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </div>
            <el-table :data="filteredDeactivatedLicenses" border size="small" style="width:100%;margin-top:8px">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="license_key" label="License Key" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span>{{ row.license_key ? row.license_key.substring(0, 20) + '...' : '--' }}</span>
                  <el-button v-if="row.license_key && !isLicenseExpired(row)" type="primary" link size="small" @click="copyText(row.license_key)">
                    <el-icon><CopyDocument /></el-icon>
                  </el-button>
                  <el-tag v-if="isLicenseExpired(row)" type="danger" size="small">{{ t('license.expired') }}</el-tag>
                  <el-tooltip v-if="!isLicenseExpired(row) && isMachineCodeChanged(row)" :content="t('license.machineCodeChangedTip')" placement="top">
                    <el-tag type="warning" size="small" style="margin-left:4px">{{ t('license.machineCodeChanged') }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="organization_name" :label="t('license.organization')" min-width="120" show-overflow-tooltip>
                <template #default="{ row }">{{ row.organization_name || '--' }}</template>
              </el-table-column>
              <el-table-column prop="license_type_name" :label="t('license.licenseType')" min-width="100" show-overflow-tooltip>
                <template #default="{ row }">{{ row.license_type_name || '--' }}</template>
              </el-table-column>
              <el-table-column :label="t('license.licenseIssuedAt')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.issued_at">{{ formatDateTime(row.issued_at) }}</span>
                  <span v-else>--</span>
                </template>
              </el-table-column>
              <el-table-column :label="t('license.appliedFeatures')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <template v-if="row.feature_names && row.feature_names.length">
                    <el-tag v-for="fn in row.feature_names" :key="fn" size="small" style="margin:2px">{{ fn }}</el-tag>
                  </template>
                  <template v-else-if="row.features && row.features.length">
                    <el-tag v-for="f in row.features" :key="f" size="small" style="margin:2px">{{ FEATURE_NAMES[f] ? t(FEATURE_NAMES[f]) : f }}</el-tag>
                  </template>
                  <span v-else>--</span>
                </template>
              </el-table-column>
              <el-table-column :label="t('license.validity')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.expiry_date">{{ formatDateTime(row.expiry_date) }}</span>
                  <span v-else>{{ t('license.permanent') }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="machine_code" :label="t('license.machineCode')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  <span>{{ row.machine_code || '--' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="deactivated_at" :label="t('license.deactivatedAt')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">{{ formatDateTime(row.deactivated_at) }}</template>
              </el-table-column>
              <el-table-column :label="t('common.operation')" min-width="140" fixed="right">
                <template #default="{ row }">
                  <el-button
                    v-if="!isLicenseExpired(row) && isMachineCodeChanged(row)"
                    type="warning"
                    size="small"
                    plain
                    :loading="replaceLicenseLoading === row.license_key"
                    @click="handleRequestReplaceLicense(row)"
                  >
                    {{ t('license.requestReplace') }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </div>

      <el-dialog
        v-model="feedbackDialogVisible"
        :title="feedbackType === 'feature' ? t('license.featureFeedback') : t('license.systemFeedbackTitle')"
        width="520px"
        :close-on-click-modal="false"
        draggable
        destroy-on-close
      >
        <el-form label-position="top">
          <el-form-item :label="t('license.clientOrg')">
            <el-input v-model="feedbackForm.organization_name" :placeholder="t('license.orgNamePlaceholder')" />
          </el-form-item>
          <el-form-item :label="t('license.clientContact')">
            <el-input v-model="feedbackForm.contact_person" :placeholder="t('license.contactPersonPlaceholder')" />
          </el-form-item>
          <el-form-item :label="t('license.contactMethod')">
            <el-input v-model="feedbackForm.contact_info" :placeholder="t('license.contactMethodPlaceholder')" />
          </el-form-item>
          <el-form-item v-if="feedbackType === 'feature'" :label="t('license.featureModule')">
            <el-input :model-value="feedbackForm.feature_module" readonly />
          </el-form-item>
          <el-form-item :label="t('license.feedbackTime')">
            <el-input :model-value="feedbackForm.feedback_time" readonly />
          </el-form-item>
          <el-form-item :label="t('license.usageFeedback')" required>
            <el-input
              v-model="feedbackForm.feedback"
              type="textarea"
              :rows="3"
              :placeholder="t('license.usageFeedbackPlaceholder')"
            />
          </el-form-item>
          <el-form-item :label="t('license.suggestionLabel')" required>
            <el-input
              v-model="feedbackForm.suggestion"
              type="textarea"
              :rows="3"
              :placeholder="t('license.suggestionPlaceholder')"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="feedbackDialogVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button
            type="primary"
            :loading="feedbackSubmitting"
            :disabled="!feedbackForm.feedback.trim() || !feedbackForm.suggestion.trim()"
            @click="handleSubmitFeedback"
          >
            <el-icon><Message /></el-icon> {{ t('license.submitFeedback') }}
          </el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import {
  ArrowLeft, ArrowRight, Key, Check, CopyDocument, Plus, Message, Warning,
  CircleCheck, Lock, ChatLineSquare, Tickets, Search,
  ChatDotSquare, DataAnalysis, Connection, TrendCharts, Money, MagicStick, Coin,
} from '@element-plus/icons-vue'
import {
  licenseState, loadLicenseStatus, activateLicense,
  deactivateLicense, deactivateFeature, applyLicense,
  getMachineCode, notifySupplierView, submitFeedback, requestReplaceLicense, FEATURES, FEATURE_NAMES, FEATURE_DESCRIPTIONS, LICENSE_TYPES,
  FEATURE_PRICES, calcTotalPrice,
}  from '@/utils/license'


const { t } = useI18n()
const router = useRouter()
 
const LAST_CONTACT_KEY = 'license_last_contact'
 
function saveLastContact() {
  const data = {
    orgName: orgName.value,
    contactPerson: contactPerson.value,
    contactPhone: contactPhone.value,
    contactEmail: contactEmail.value,
    contactWechat: contactWechat.value,
    remarks: remarks.value,
  }
  localStorage.setItem(LAST_CONTACT_KEY, JSON.stringify(data))
}
 
function loadLastContact() {
  try {
    const raw = localStorage.getItem(LAST_CONTACT_KEY)
    if (raw) {
      const data = JSON.parse(raw)
      orgName.value = data.orgName || ''
      contactPerson.value = data.contactPerson || ''
      contactPhone.value = data.contactPhone || ''
      contactEmail.value = data.contactEmail || ''
      contactWechat.value = data.contactWechat || ''
      remarks.value = data.remarks || ''
    }
  } catch {
    // ignore
  }
}
 
function goBack() {
  router.back()
}
const machineCode = ref('')
const licenseKeyInput = ref('')
const activating = ref(false)
const deactivating = ref(false)
const addonLicenseKey = ref('')
const addonActivating = ref(false)
const featureDeactivating = ref(null)
const selectedFeatures = ref([])
const addonSelectedFeatures = ref([])
const selectedLicenseType = ref('')
const addonLicenseType = ref('')
const applyReferralCode = ref('')
const addonReferralCode = ref('')
const applyingLicense = ref(false)
const addonApplying = ref(false)
const orgName = ref('')
const contactPerson = ref('')
const contactPhone = ref('')
const contactWechat = ref('')
const contactEmail = ref('')
const remarks = ref('')
const activeCollapse = ref([])
const deactivatedCollapse = ref([])
const deactivatedStatusFilter = ref('unexpired')
const deactivatedSearchKeyword = ref('')
const showSupplierInfo = ref(false)
const inputMachineCode = ref('')
const showAddonSupplierInfo = ref(false)
const inputAddonMachineCode = ref('')
const allFeatureOptions = [
  { key: FEATURES.GRADE_TREND, name: FEATURE_NAMES[FEATURES.GRADE_TREND], icon: TrendCharts },
  { key: FEATURES.FEE_MANAGEMENT, name: FEATURE_NAMES[FEATURES.FEE_MANAGEMENT], icon: Money },
  { key: FEATURES.SMART_SCHEDULING, name: FEATURE_NAMES[FEATURES.SMART_SCHEDULING], icon: MagicStick },
  { key: FEATURES.WECHAT_NOTIFY, name: FEATURE_NAMES[FEATURES.WECHAT_NOTIFY], icon: Connection },
  { key: FEATURES.SMART_COMMAND, name: FEATURE_NAMES[FEATURES.SMART_COMMAND], icon: ChatDotSquare },
  { key: FEATURES.DASHBOARD_VIEW, name: FEATURE_NAMES[FEATURES.DASHBOARD_VIEW], icon: DataAnalysis },
  { key: FEATURES.FLOATING_SPHERE, name: FEATURE_NAMES[FEATURES.FLOATING_SPHERE], icon: CircleCheck },
  { key: FEATURES.DATABASE_MANAGEMENT, name: FEATURE_NAMES[FEATURES.DATABASE_MANAGEMENT], icon: Coin },
  { key: FEATURES.STUDENT_EVALUATION, name: FEATURE_NAMES[FEATURES.STUDENT_EVALUATION], icon: DataAnalysis },
]
const defaultModules = computed(() => [
  t('license.defaultModuleCourse'), t('license.defaultModuleTeacher'), t('license.defaultModuleStudent'), t('license.defaultModuleClass'), t('license.defaultModuleRoom'), t('license.defaultModuleHoliday'), t('license.defaultModuleCondition'), t('license.defaultModuleSchedule'), t('license.defaultModuleSearch'),
  t('license.defaultModuleBatchImport'), t('license.defaultModuleExport'), t('license.defaultModuleCalendarView'), t('license.defaultModuleListView'), t('license.defaultModuleUserMgmt'), t('license.defaultModuleLogMgmt'), t('license.defaultModulePromotion'), t('license.defaultModuleEmail'),
  t('license.defaultModuleResponsive'), t('license.defaultModuleI18n')
])
const addonFeatureOptions = computed(() =>
  allFeatureOptions.filter(opt => !licenseState.features[opt.key])
)
const featureList = computed(() => [
  { key: FEATURES.GRADE_TREND, name: FEATURE_NAMES[FEATURES.GRADE_TREND], icon: TrendCharts, enabled: !!licenseState.features[FEATURES.GRADE_TREND] },
  { key: FEATURES.FEE_MANAGEMENT, name: FEATURE_NAMES[FEATURES.FEE_MANAGEMENT], icon: Money, enabled: !!licenseState.features[FEATURES.FEE_MANAGEMENT] },
  { key: FEATURES.SMART_SCHEDULING, name: FEATURE_NAMES[FEATURES.SMART_SCHEDULING], icon: MagicStick, enabled: !!licenseState.features[FEATURES.SMART_SCHEDULING] },
  { key: FEATURES.WECHAT_NOTIFY, name: FEATURE_NAMES[FEATURES.WECHAT_NOTIFY], icon: Connection, enabled: !!licenseState.features[FEATURES.WECHAT_NOTIFY] },
  { key: FEATURES.SMART_COMMAND, name: FEATURE_NAMES[FEATURES.SMART_COMMAND], icon: ChatDotSquare, enabled: !!licenseState.features[FEATURES.SMART_COMMAND] },
  { key: FEATURES.DASHBOARD_VIEW, name: FEATURE_NAMES[FEATURES.DASHBOARD_VIEW], icon: DataAnalysis, enabled: !!licenseState.features[FEATURES.DASHBOARD_VIEW] },
  { key: FEATURES.FLOATING_SPHERE, name: FEATURE_NAMES[FEATURES.FLOATING_SPHERE], icon: CircleCheck, enabled: !!licenseState.features[FEATURES.FLOATING_SPHERE] },
  { key: FEATURES.DATABASE_MANAGEMENT, name: FEATURE_NAMES[FEATURES.DATABASE_MANAGEMENT], icon: Coin, enabled: !!licenseState.features[FEATURES.DATABASE_MANAGEMENT] },
  { key: FEATURES.STUDENT_EVALUATION, name: FEATURE_NAMES[FEATURES.STUDENT_EVALUATION], icon: DataAnalysis, enabled: !!licenseState.features[FEATURES.STUDENT_EVALUATION] },
])

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  let d
  if (dateStr.includes('T')) {
    d = new Date(dateStr + (dateStr.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(dateStr) ? '' : 'Z'))
  } else {
    d = new Date(dateStr)
  }
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
async function copyMachineCode() {
  try {
    await navigator.clipboard.writeText(machineCode.value)
    ElMessage.success(t('license.machineCodeCopied'))
  } catch {
    ElMessage.error(t('license.copyFailed'))
  }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(t('license.copiedToClipboard'))
  } catch {
    ElMessage.error(t('license.copyFailed'))
  }
}

const filteredDeactivatedLicenses = computed(() => {
  let list = licenseState.deactivatedLicenses
  if (deactivatedStatusFilter.value === 'unexpired') {
    list = list.filter(r => !isLicenseExpired(r))
  } else if (deactivatedStatusFilter.value === 'expired') {
    list = list.filter(r => isLicenseExpired(r))
  }
  const kw = deactivatedSearchKeyword.value.trim().toLowerCase()
  if (kw) {
    list = list.filter(r => {
      const org = (r.organization_name || '').toLowerCase()
      const type = (r.license_type_name || '').toLowerCase()
      const feats = (r.feature_names || r.features || []).join(' ').toLowerCase()
      return org.includes(kw) || type.includes(kw) || feats.includes(kw)
    })
  }
  return list
})

function isLicenseExpired(row) {
  if (!row.expiry_date) return false
  const expiryStr = row.expiry_date
  const expiryDate = expiryStr.includes('T') ? new Date(expiryStr + (expiryStr.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(expiryStr) ? '' : 'Z')) : new Date(expiryStr + 'T23:59:59Z')
  return expiryDate < new Date()
}

function isMachineCodeChanged(row) {
  if (!row.machine_code) return false
  return row.machine_code !== licenseState.machineCode
}

const replaceLicenseLoading = ref('')

async function handleRequestReplaceLicense(row) {
  try {
    await ElMessageBox.confirm(
      t('license.confirmReplaceLicense'),
      t('license.replaceLicenseTitle'),
      { confirmButtonText: t('license.confirmApply'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
  } catch {
    return
  }
  replaceLicenseLoading.value = row.license_key
  try {
    const result = await requestReplaceLicense({
      organization_name: row.organization_name || orgName.value || '',
      contact_person: contactPerson.value || '',
      original_license_key: row.license_key || '',
      license_type_name: row.license_type_name || '',
      original_machine_code: row.machine_code || '',
      expiry_date: row.expiry_date || '',
    })
    const msgs = [t('license.replaceRequestSubmitted')]
    if (result.webhook_sent) msgs.push(t('license.webhookSent'))
    if (result.email_sent) msgs.push(t('license.emailSent'))
    ElMessage.success(msgs.join('，'))
  } catch (error) {
    const detail = error.response?.data?.detail || t('license.replaceFailed')
    ElMessage.error(detail)
  } finally {
    replaceLicenseLoading.value = ''
  }
}
 
function isOwnReferralCode(code) {
  if (!code || !code.trim()) return false
  if (!licenseState.referralCode) return false
  return code.trim() === licenseState.referralCode.trim()
}

function toggleFeature(key) {
  const idx = selectedFeatures.value.indexOf(key)
  if (idx >= 0) {
    selectedFeatures.value.splice(idx, 1)
  } else {
    selectedFeatures.value.push(key)
  }
}
 
function toggleAddonFeature(key) {
  const idx = addonSelectedFeatures.value.indexOf(key)
  if (idx >= 0) {
    addonSelectedFeatures.value.splice(idx, 1)
  } else {
    addonSelectedFeatures.value.push(key)
  }
}

async function verifyMachineCode() {
  if (!inputMachineCode.value.trim()) {
    ElMessage.warning(t('license.inputMachineCode'))
    return
  }
  if (inputMachineCode.value.trim() === machineCode.value.trim()) {
    showSupplierInfo.value = true
    try {
      await notifySupplierView({
        organization_name: orgName.value || t('license.unfilled'),
        contact_person: contactPerson.value || t('license.unfilled'),
        contact_phone: contactPhone.value || '',
        contact_email: contactEmail.value || '',
        contact_wechat: contactWechat.value || '',
        machine_code: machineCode.value,
        view_time: new Date().toLocaleString('zh-CN'),
      })
    } catch {
      // webhook发送失败不影响用户查看
    }
    ElMessage.success(t('license.machineCodeVerified'))
  } else {
    ElMessage.error(t('license.machineCodeError'))
  }
}

async function verifyAddonMachineCode() {
  if (!inputAddonMachineCode.value.trim()) {
    ElMessage.warning(t('license.inputMachineCode'))
    return
  }
  if (inputAddonMachineCode.value.trim() === machineCode.value.trim()) {
    showAddonSupplierInfo.value = true
    try {
      await notifySupplierView({
        organization_name: orgName.value || t('license.unfilled'),
        contact_person: contactPerson.value || t('license.unfilled'),
        contact_phone: contactPhone.value || '',
        contact_email: contactEmail.value || '',
        contact_wechat: contactWechat.value || '',
        machine_code: machineCode.value,
        view_time: new Date().toLocaleString('zh-CN'),
      })
    } catch {
      // webhook发送失败不影响用户查看
    }
    ElMessage.success(t('license.machineCodeVerified'))
  } else {
    ElMessage.error(t('license.machineCodeError'))
  }
}
async function handleApplyLicense() {
  if (!selectedFeatures.value.length) {
    ElMessage.warning(t('license.selectOneModule'))
    return
  }
  if (!orgName.value) {
    ElMessage.warning(t('license.fillOrgName'))
    return
  }
  if (!contactPerson.value) {
    ElMessage.warning(t('license.fillContactPerson'))
    return
  }
  if (!contactPhone.value && !contactEmail.value && !contactWechat.value) {
    ElMessage.warning(t('license.fillOneContact'))
    return
  }
  if (!selectedLicenseType.value) {
    ElMessage.warning(t('license.selectLicenseType'))
    return
  }
  if (applyReferralCode.value && licenseState.referralCode && applyReferralCode.value.trim() === licenseState.referralCode.trim()) {
    ElMessage.warning(t('license.cannotUseOwnReferralCode'))
    return
  }
  applyingLicense.value = true
  try {
    await applyLicense({
      organization_name: orgName.value,
      contact_person: contactPerson.value,
      contact_phone: contactPhone.value,
      contact_email: contactEmail.value,
      contact_wechat: contactWechat.value,
      remarks: remarks.value,
    }, selectedFeatures.value, 'new', selectedLicenseType.value, applyReferralCode.value.trim())
    ElMessage.success(t('license.applySuccess'))
    saveLastContact()
  } catch (error) {
    const detail = error.response?.data?.detail || t('license.applyFailed')
    ElMessage.error(detail)
  } finally {
    applyingLicense.value = false
  }
}
 
async function handleApplyAddon() {
  if (!addonSelectedFeatures.value.length) {
    ElMessage.warning(t('license.selectOneModule'))
    return
  }
  if (!orgName.value) {
    ElMessage.warning(t('license.fillOrgName'))
    return
  }
  if (!contactPerson.value) {
    ElMessage.warning(t('license.fillContactPerson'))
    return
  }
  if (!contactPhone.value && !contactEmail.value && !contactWechat.value) {
    ElMessage.warning(t('license.fillOneContact'))
    return
  }
  if (!addonLicenseType.value) {
    ElMessage.warning(t('license.selectLicenseType'))
    return
  }
  if (addonReferralCode.value && licenseState.referralCode && addonReferralCode.value.trim() === licenseState.referralCode.trim()) {
    ElMessage.warning(t('license.cannotUseOwnReferralCode'))
    return
  }
  addonApplying.value = true
  try {
    await applyLicense({
      organization_name: orgName.value,
      contact_person: contactPerson.value,
      contact_phone: contactPhone.value,
      contact_email: contactEmail.value,
      contact_wechat: contactWechat.value,
      remarks: remarks.value,
    }, addonSelectedFeatures.value, 'addon', addonLicenseType.value, addonReferralCode.value.trim())
    ElMessage.success(t('license.addonApplySuccess'))
    saveLastContact()
  } catch (error) {
    const detail = error.response?.data?.detail || t('license.applyFailed')
    ElMessage.error(detail)
  } finally {
    addonApplying.value = false
  }
}
async function handleActivate() {
  if (!licenseKeyInput.value.trim()) {
    ElMessage.warning(t('license.inputLicenseKey'))
    return
  }
  activating.value = true
  try {
    const result = await activateLicense(licenseKeyInput.value.trim(), selectedFeatures.value, {
      organization_name: orgName.value,
      contact_person: contactPerson.value,
      contact_phone: contactPhone.value,
      contact_email: contactEmail.value,
      contact_wechat: contactWechat.value,
      remarks: remarks.value,
    })
    ElMessage.success(t('license.activateSuccess', { type: result.license_type_name }))
    saveLastContact()
    licenseKeyInput.value = ''
    selectedFeatures.value = []
    selectedLicenseType.value = ''
  } catch (error) {
    const detail = error.response?.data?.detail || t('license.activateFailed')
    ElMessage.error(detail)
  } finally {
    activating.value = false
  }
}

async function handleAddonActivate() {
  if (!addonLicenseKey.value.trim()) {
    ElMessage.warning(t('license.inputAddonLicenseKey'))
    return
  }
  if (!addonSelectedFeatures.value.length) {
    ElMessage.warning(t('license.selectOneFeature'))
    return
  }
  addonActivating.value = true
  try {
    const result = await activateLicense(addonLicenseKey.value.trim(), addonSelectedFeatures.value, {
      organization_name: orgName.value,
      contact_person: contactPerson.value,
      contact_phone: contactPhone.value,
      contact_email: contactEmail.value,
      contact_wechat: contactWechat.value,
      remarks: remarks.value,
    })
    ElMessage.success(t('license.addonActivateSuccess', { type: result.license_type_name }))
    saveLastContact()
    addonLicenseKey.value = ''
    addonSelectedFeatures.value = []
    addonLicenseType.value = ''
  } catch (error) {
    const detail = error.response?.data?.detail || t('license.addonActivateFailed')
    ElMessage.error(detail)
  } finally {
    addonActivating.value = false
  }
}

async function handleDeactivateFeature(feat) {
  try {
    const enabledCount = Object.values(licenseState.features).filter(Boolean).length
    let confirmMsg = t('license.confirmDeactivateFeature', { name: t(feat.name) })
    if (enabledCount > 1) {
      confirmMsg = t('license.confirmDeactivateFeatureMulti', { count: enabledCount, name: t(feat.name), features: Object.entries(licenseState.features).filter(([,v]) => v).map(([k]) => FEATURE_NAMES[k] ? t(FEATURE_NAMES[k]) : k).join('、') })
    }
    await ElMessageBox.confirm(
      confirmMsg,
      t('license.confirmDeactivateTitle'),
      { confirmButtonText: t('license.confirmDeactivate'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
    featureDeactivating.value = feat.key
    await deactivateLicense()
    ElMessage.success(t('license.licenseDeactivatedAll'))
  } catch {
    // 取消
  } finally {
    featureDeactivating.value = null
  }
}

async function handleDeactivate() {
  try {
    await ElMessageBox.confirm(
      t('license.confirmDeactivateLicense'),
      t('license.confirmDeactivateTitle'),
      { confirmButtonText: t('license.confirmDeactivate'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
    deactivating.value = true
    await deactivateLicense()
    ElMessage.success(t('license.licenseDeactivated'))
  } catch {
    // 取消
  } finally {
    deactivating.value = false
  }
}

const feedbackDialogVisible = ref(false)
const feedbackType = ref('feature')
const feedbackSubmitting = ref(false)
const feedbackForm = ref({
  organization_name: '',
  contact_person: '',
  contact_info: '',
  feature_module: '',
  feedback_time: '',
  feedback: '',
  suggestion: '',
})

function getCurrentTimeStr() {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

function openFeatureFeedbackDialog(feat) {
  feedbackType.value = 'feature'
  feedbackForm.value = {
    organization_name: licenseState.organizationName || orgName.value || '',
    contact_person: contactPerson.value || '',
    contact_info: contactPhone.value || contactEmail.value || contactWechat.value || '',
    feature_module: t(feat.name),
    feedback_time: getCurrentTimeStr(),
    feedback: '',
    suggestion: '',
  }
  feedbackDialogVisible.value = true
}

function openSystemFeedbackDialog() {
  feedbackType.value = 'system'
  feedbackForm.value = {
    organization_name: licenseState.organizationName || orgName.value || '',
    contact_person: contactPerson.value || '',
    contact_info: contactPhone.value || contactEmail.value || contactWechat.value || '',
    feature_module: t('license.systemFeedbackTitle'),
    feedback_time: getCurrentTimeStr(),
    feedback: '',
    suggestion: '',
  }
  feedbackDialogVisible.value = true
}

async function handleSubmitFeedback() {
  if (!feedbackForm.value.feedback.trim()) {
    ElMessage.warning(t('license.fillFeedback'))
    return
  }
  if (!feedbackForm.value.suggestion.trim()) {
    ElMessage.warning(t('license.fillSuggestion'))
    return
  }
  feedbackSubmitting.value = true
  try {
    const result = await submitFeedback({
      organization_name: feedbackForm.value.organization_name || undefined,
      contact_person: feedbackForm.value.contact_person || undefined,
      contact_info: feedbackForm.value.contact_info || undefined,
      feature_module: feedbackForm.value.feature_module || undefined,
      feedback_time: feedbackForm.value.feedback_time || undefined,
      feedback: feedbackForm.value.feedback,
      suggestion: feedbackForm.value.suggestion || undefined,
      feedback_type: feedbackType.value,
    })
    const msgs = [t('license.feedbackSubmitted')]
    if (result.webhook_sent) msgs.push(t('license.webhookSent'))
    if (result.email_sent) msgs.push(t('license.emailSent'))
    ElMessage.success(msgs.join('，'))
    feedbackDialogVisible.value = false
  } catch (error) {
    const detail = error.response?.data?.detail || t('license.feedbackSubmitFailed')
    ElMessage.error(detail)
  } finally {
    feedbackSubmitting.value = false
  }
}

onMounted(async () => {
  loadLastContact()
  await loadLicenseStatus()
  machineCode.value = licenseState.machineCode || await getMachineCode()
  if (!orgName.value) {
    orgName.value = licenseState.organizationName || licenseState.siteName || localStorage.getItem('site_name') || ''
  }
  if (!contactPerson.value) {
    contactPerson.value = licenseState.contactPerson || ''
  }
  if (!contactPhone.value) {
    contactPhone.value = licenseState.contactPhone || ''
  }
  if (!contactEmail.value) {
    contactEmail.value = licenseState.contactEmail || ''
  }
  if (!contactWechat.value) {
    contactWechat.value = licenseState.contactWechat || ''
  }
})
</script>

<style scoped>
.license-page {
  padding: 20px;
  min-height: 100vh;
  box-sizing: border-box;
}
.license-card {
  border-radius: 12px;
  max-width: 1400px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
}
.license-status p {
  margin: 4px 0;
}
.deactivated-filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
.referral-code-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fdf6ec 0%, #fef9f0 100%);
  border: 1px solid #f5dab1;
  border-radius: 8px;
}
.referral-code-main {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
.referral-code-hint {
  font-size: 13px;
  line-height: 1.6;
}
.feature-card {
  text-align: center;
  padding: 12px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.feature-card.enabled {
  border-color: #67c23a;
  background: #f0f9eb;
}
.feature-card.disabled {
  border-color: #dcdfe6;
  opacity: 0.6;
}
.feature-card.selectable {
  cursor: pointer;
  transition: all 0.25s;
  border: 2px solid #dcdfe6;
}
.feature-card.selectable.selected {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
}
.feature-card.selectable:not(.selected):hover {
  border-color: #c6e2ff;
  background: #f5f7fa;
}
.default-modules-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.default-module-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
  color: #67c23a;
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}
.default-module-tag .el-icon {
  font-size: 14px;
}
.addon-title-btn {
  animation: pulse 1.5s ease-in-out infinite;
  font-weight: bold;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(103, 194, 58, 0.6); }
  50%      { box-shadow: 0 0 0 10px rgba(103, 194, 58, 0); }
}

.steps-container {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-top: 20px;
}
.step-card {
  flex: 1;
  min-width: 0;
  background: #fafafa;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  overflow: hidden;
}
.step-card-wide {
  flex: 1.2;
}
.step-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  font-weight: bold;
  font-size: 15px;
}
.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255,255,255,0.3);
  font-size: 14px;
  font-weight: bold;
}
.step-title {
  font-size: 15px;
}
.step-body {
  padding: 16px;
}
.step-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  padding-top: 14px;
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .steps-container {
    flex-direction: column;
  }
  .step-arrow {
    transform: rotate(90deg);
    padding-top: 0;
    align-self: center;
  }
  .step-card {
    width: 100%;
  }
  .step-card-wide {
    flex: none;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .license-page {
    padding: 10px;
  }
  .card-header {
    font-size: 15px;
    flex-wrap: wrap;
  }
  .step-header {
    padding: 10px 14px;
    font-size: 13px;
  }
  .step-body {
    padding: 12px;
  }
}

.supplier-mask-wrapper {
  position: relative;
  min-height: 120px;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7fa;
}

.supplier-mask-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}

.supplier-mask-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
</style>