<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  LucidePaperclip,
  LucideFolder,
  LucideFolderOpen,
  LucideFileText,
  LucideImage,
  LucideDownload,
  LucideEye,
  LucideLock,
  LucideUnlock,
  LucideUpload,
} from 'lucide-vue-next'
import { apiCall } from '@/api'
import { Card, Button, Skeleton } from '@/components/ui'

const props = defineProps<{ vehicleId: string }>()

const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const isLoading = ref(true)
const attachmentsData = ref<any>(null)
const activeFolder = ref<string | null>(null)
const viewMode = ref<'folders' | 'table'>('folders')
const targetFolder = ref<string | null>(null)
const draggingFile = ref<any>(null)
const dragOverFolder = ref<string | null>(null)

const folderConfig = [
  { id: 'registration', label: 'Registration & Licensing', icon: LucideFileText },
  { id: 'insurance', label: 'Insurance', icon: LucideFileText },
  { id: 'contracts', label: 'Purchase / Lease Contracts', icon: LucideFileText },
  { id: 'certificates', label: 'Inspection Certificates', icon: LucideFileText },
  { id: 'reports', label: 'External Reports', icon: LucideFileText },
  { id: 'other', label: 'Other', icon: LucideFolder },
]

async function loadAttachments() {
  isLoading.value = true
  try {
    attachmentsData.value = await apiCall('car_repair_management.api.vehicle.get_vehicle_attachments', {
      vehicle_name: props.vehicleId,
    })
  } catch (e) {
    console.error('Failed to load attachments', e)
  } finally {
    isLoading.value = false
  }
}

function formatFileSize(bytes: number | null): string {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getFileIcon(type: string) {
  const imageTypes = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']
  if (imageTypes.includes(type.toLowerCase())) return LucideImage
  return LucideFileText
}

function toggleFolder(folderId: string) {
  activeFolder.value = activeFolder.value === folderId ? null : folderId
}

function previewFile(file: any) {
  if (file.file_url) window.open(file.file_url, '_blank')
}

function triggerUpload(folderId?: string) {
  targetFolder.value = folderId || null
  fileInput.value?.click()
}

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  isUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('doctype', 'Vehicle')
    formData.append('docname', props.vehicleId)
    formData.append('is_private', '0')

    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'X-Frappe-Site-Name': window.location.hostname,
    }
    const csrfToken = (window as any).csrf_token
    if (csrfToken && csrfToken !== '{{ csrf_token }}') {
      headers['X-Frappe-CSRF-Token'] = csrfToken
    }

    const response = await fetch('/api/method/upload_file', {
      method: 'POST',
      headers,
      credentials: 'include',
      body: formData,
    })

    const responseData = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(responseData.message || response.statusText)
    }

    if (targetFolder.value) {
      const fileUrl = responseData?.message?.file_url
      if (fileUrl) {
        await apiCall('car_repair_management.api.vehicle.upload_vehicle_attachment', {
          vehicle_name: props.vehicleId,
          file_url: fileUrl,
          category: targetFolder.value,
        })
      }
    }

    await loadAttachments()
  } catch (e) {
    console.error('Failed to upload file', e)
  } finally {
    isUploading.value = false
    input.value = ''
  }
}

function downloadFile(file: any) {
  if (file.file_url) {
    const link = document.createElement('a')
    link.href = file.file_url
    link.download = file.file_name
    link.click()
  }
}

function onDragStart(file: any, event: DragEvent) {
  draggingFile.value = file
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function onDragEnd() {
  draggingFile.value = null
  dragOverFolder.value = null
}

function onDragOver(folderId: string) {
  dragOverFolder.value = folderId
}

async function onDrop(targetFolderId: string) {
  dragOverFolder.value = null
  if (!draggingFile.value) return

  try {
    await apiCall('car_repair_management.api.vehicle.move_vehicle_attachment', {
      file_name: draggingFile.value.name,
      vehicle_name: props.vehicleId,
      target_category: targetFolderId,
    })
    await loadAttachments()
  } catch (e) {
    console.error('Failed to move file', e)
  } finally {
    draggingFile.value = null
  }
}

const totalFiles = computed(() => attachmentsData.value?.total || 0)

const folderFiles = computed(() => {
  if (!activeFolder.value || !attachmentsData.value?.folders) return []
  return attachmentsData.value.folders[activeFolder.value] || []
})

onMounted(loadAttachments)
</script>

<template>
  <div class="space-y-6">
    <input ref="fileInput" type="file" class="hidden" @change="uploadFile" />

    <!-- Loading State -->
    <template v-if="isLoading">
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card v-for="i in 6" :key="i"><Skeleton height="100px" /></Card>
      </div>
    </template>

    <template v-else-if="attachmentsData">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold" style="color: var(--text-primary);">
            <LucidePaperclip class="inline size-5 mr-2" />
            Document Library
          </h3>
          <p class="text-sm" style="color: var(--text-muted);">{{ totalFiles }} files attached</p>
        </div>
        <div class="flex items-center gap-2">
          <Button variant="outline" size="sm" @click="viewMode = viewMode === 'folders' ? 'table' : 'folders'">
            {{ viewMode === 'folders' ? 'Table View' : 'Folder View' }}
          </Button>
          <Button @click="triggerUpload" :disabled="isUploading">
            <LucideUpload class="size-4" />
            {{ isUploading ? 'Uploading…' : 'Upload' }}
          </Button>
        </div>
      </div>

      <!-- Folder View -->
      <template v-if="viewMode === 'folders'">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <button
            v-for="folder in folderConfig"
            :key="folder.id"
            @click="toggleFolder(folder.id)"
            @dragover.prevent="onDragOver(folder.id)"
            @dragleave="dragOverFolder = null"
            @drop.prevent="onDrop(folder.id)"
            :class="[
              'p-4 rounded-lg border text-left transition-colors hover:opacity-80',
              activeFolder === folder.id ? 'ring-2 ring-blue-500' : '',
              dragOverFolder === folder.id ? 'ring-2 ring-green-500 opacity-90' : '',
            ]"
            :style="{
              backgroundColor: 'var(--bg-tertiary)',
              borderColor: activeFolder === folder.id ? 'var(--accent)' : 'var(--border-color)',
            }"
          >
            <div class="flex items-center gap-3">
              <component
                :is="activeFolder === folder.id ? LucideFolderOpen : LucideFolder"
                class="size-8"
                style="color: var(--text-muted);"
              />
              <div>
                <p class="text-sm font-medium" style="color: var(--text-primary);">{{ folder.label }}</p>
                <p class="text-xs" style="color: var(--text-muted);">
                  {{ attachmentsData.counts?.[folder.id] || 0 }} files
                </p>
              </div>
            </div>
          </button>
        </div>

        <!-- Folder Contents -->
        <Card v-if="activeFolder" padding="none">
          <div class="p-4 border-b flex items-center justify-between" style="border-color: var(--border-color);">
            <h4 class="text-sm font-semibold" style="color: var(--text-primary);">
              {{ folderConfig.find(f => f.id === activeFolder)?.label }}
            </h4>
            <Button size="sm" @click="triggerUpload(activeFolder)" :disabled="isUploading">
              <LucideUpload class="size-4" />
              {{ isUploading ? 'Uploading…' : 'Upload Here' }}
            </Button>
          </div>

          <div v-if="folderFiles.length" class="divide-y" style="--tw-divide-color: var(--border-subtle);">
            <div
              v-for="file in folderFiles"
              :key="file.name"
              draggable="true"
              @dragstart="onDragStart(file, $event)"
              @dragend="onDragEnd"
              class="flex items-center justify-between p-4 hover:opacity-80 transition-colors cursor-grab"
              :class="{ 'opacity-50': draggingFile?.name === file.name }"
            >
              <div class="flex items-center gap-3">
                <component :is="getFileIcon(file.type)" class="size-8" style="color: var(--text-muted);" />
                <div>
                  <p class="text-sm font-medium" style="color: var(--text-primary);">{{ file.file_name }}</p>
                  <div class="flex items-center gap-3 text-xs" style="color: var(--text-muted);">
                    <span>{{ file.type }}</span>
                    <span>{{ formatFileSize(file.size) }}</span>
                    <span>{{ file.uploaded_by }}</span>
                    <span>{{ file.upload_date }}</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <Button variant="ghost" size="sm" @click="previewFile(file)" title="Preview">
                  <LucideEye class="size-4" />
                </Button>
                <Button variant="ghost" size="sm" @click="downloadFile(file)" title="Download">
                  <LucideDownload class="size-4" />
                </Button>
                <component
                  :is="file.is_private ? LucideLock : LucideUnlock"
                  class="size-4"
                  style="color: var(--text-muted);"
                  :title="file.is_private ? 'Private' : 'Public'"
                />
              </div>
            </div>
          </div>

          <div v-else class="p-8 text-center">
            <LucideFolder class="size-12 mx-auto mb-4" style="color: var(--text-muted);" />
            <p class="text-sm" style="color: var(--text-muted);">No files in this folder</p>
          </div>
        </Card>
      </template>

      <!-- Table View -->
      <template v-else>
        <Card padding="none">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b" style="border-color: var(--border-color);">
                  <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">File Name</th>
                  <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Type</th>
                  <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Category</th>
                  <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Uploaded By</th>
                  <th class="text-left px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Date</th>
                  <th class="text-right px-4 py-3 text-xs uppercase tracking-wide" style="color: var(--text-muted);">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="file in attachmentsData.files"
                  :key="file.name"
                  class="border-b"
                  style="border-color: var(--border-subtle);"
                >
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                      <component :is="getFileIcon(file.type)" class="size-5" style="color: var(--text-muted);" />
                      <span class="text-sm font-medium" style="color: var(--text-primary);">{{ file.file_name }}</span>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-sm" style="color: var(--text-secondary);">{{ file.type }}</td>
                  <td class="px-4 py-3">
                    <span
                      class="px-2 py-1 rounded text-xs font-medium"
                      style="background-color: var(--bg-tertiary); color: var(--text-secondary);"
                    >
                      {{ file.category }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-sm" style="color: var(--text-secondary);">{{ file.uploaded_by }}</td>
                  <td class="px-4 py-3 text-sm" style="color: var(--text-muted);">{{ file.upload_date }}</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-end gap-1">
                      <Button variant="ghost" size="sm" @click="previewFile(file)" title="Preview">
                        <LucideEye class="size-4" />
                      </Button>
                      <Button variant="ghost" size="sm" @click="downloadFile(file)" title="Download">
                        <LucideDownload class="size-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Empty State -->
          <div v-if="!attachmentsData.files?.length" class="p-12 text-center">
            <LucidePaperclip class="size-12 mx-auto mb-4" style="color: var(--text-muted);" />
            <h3 class="text-lg font-semibold mb-2" style="color: var(--text-primary);">No Attachments</h3>
            <p class="text-sm mb-4" style="color: var(--text-muted);">No documents have been attached to this vehicle.</p>
            <Button @click="triggerUpload" :disabled="isUploading">
              <LucideUpload class="size-4" />
              {{ isUploading ? 'Uploading…' : 'Upload Document' }}
            </Button>
          </div>
        </Card>
      </template>
    </template>
  </div>
</template>
