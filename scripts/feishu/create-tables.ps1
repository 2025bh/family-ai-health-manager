param(
    [string]$BaseToken = 'NUXQbSoUoaawZksn4bLcJI5In7g'
)

$ErrorActionPreference = 'Stop'

function Escape-NativeJson([object]$Value) {
    $json = $Value | ConvertTo-Json -Compress -Depth 20
    return $json.Replace('"', '\"')
}

function Get-TableList {
    $raw = & lark-cli base +table-list --base-token $BaseToken --as user
    if ($LASTEXITCODE -ne 0) { throw '读取飞书数据表失败' }
    return ($raw | ConvertFrom-Json).data.items
}

function New-BaseTable([string]$Name, [object[]]$Fields) {
    $escaped = Escape-NativeJson $Fields
    & lark-cli base +table-create --base-token $BaseToken --name $Name --fields $escaped --as user
    if ($LASTEXITCODE -ne 0) { throw "创建数据表失败：$Name" }
}

function Add-MissingFields([string]$TableId, [object[]]$Fields) {
    $raw = & lark-cli base +field-list --base-token $BaseToken --table-id $TableId --as user
    if ($LASTEXITCODE -ne 0) { throw "读取字段失败：$TableId" }
    $parsed = $raw | ConvertFrom-Json
    $names = @($parsed.data.items | ForEach-Object { $_.field_name })
    foreach ($field in $Fields) {
        if ($names -contains $field.name) { continue }
        $escaped = Escape-NativeJson $field
        & lark-cli base +field-create --base-token $BaseToken --table-id $TableId --json $escaped --as user
        if ($LASTEXITCODE -ne 0) { throw "创建字段失败：$($field.name)" }
    }
}

$sourceOptions = @(
    @{ name = 'user_reported'; hue = 'Blue'; lightness = 'Lighter' },
    @{ name = 'family_reported'; hue = 'Turquoise'; lightness = 'Lighter' },
    @{ name = 'doctor_reported'; hue = 'Green'; lightness = 'Lighter' },
    @{ name = 'uploaded_document'; hue = 'Purple'; lightness = 'Lighter' },
    @{ name = 'device_measurement'; hue = 'Orange'; lightness = 'Lighter' },
    @{ name = 'ai_inferred'; hue = 'Gray'; lightness = 'Lighter' }
)

$schemas = [ordered]@{
    '家庭成员' = @(
        @{ type = 'text'; name = 'member_id'; description = 'FamilyCare DB 中的成员 ID' },
        @{ type = 'text'; name = '姓名' },
        @{ type = 'text'; name = '关系' },
        @{ type = 'text'; name = '常用称呼' },
        @{ type = 'updated_at'; name = '同步更新时间'; style = @{ format = 'yyyy-MM-dd HH:mm' } }
    )
    '健康日志' = @(
        @{ type = 'text'; name = 'log_id' },
        @{ type = 'text'; name = 'member_id' },
        @{ type = 'select'; name = '类型'; multiple = $false; options = @('symptom','sleep','food','exercise','mood','bowel','medication','other' | ForEach-Object { @{ name = $_ } }) },
        @{ type = 'text'; name = '老人原话'; description = '永久保留，不能被 AI 结构化结果覆盖' },
        @{ type = 'text'; name = '结构化结果JSON' },
        @{ type = 'select'; name = '来源'; multiple = $false; options = $sourceOptions },
        @{ type = 'checkbox'; name = '可能紧急' },
        @{ type = 'datetime'; name = '发生时间'; style = @{ format = 'yyyy-MM-dd HH:mm' } }
    )
    '健康测量' = @(
        @{ type = 'text'; name = 'measurement_id' },
        @{ type = 'text'; name = 'member_id' },
        @{ type = 'select'; name = '类型'; multiple = $false; options = @('blood_pressure','blood_glucose','weight','temperature' | ForEach-Object { @{ name = $_ } }) },
        @{ type = 'number'; name = '数值1'; style = @{ type = 'plain'; precision = 2 } },
        @{ type = 'number'; name = '数值2'; style = @{ type = 'plain'; precision = 2 } },
        @{ type = 'text'; name = '单位' },
        @{ type = 'select'; name = '测量场景'; multiple = $false; options = @('fasting','post_meal','random','resting','unknown' | ForEach-Object { @{ name = $_ } }) },
        @{ type = 'text'; name = '原话' },
        @{ type = 'select'; name = '来源'; multiple = $false; options = $sourceOptions },
        @{ type = 'datetime'; name = '测量时间'; style = @{ format = 'yyyy-MM-dd HH:mm' } }
    )
    '就医记录' = @(
        @{ type = 'text'; name = 'visit_id' },
        @{ type = 'text'; name = 'member_id' },
        @{ type = 'select'; name = '状态'; multiple = $false; options = @('PREPARING','READY','VISITED','FOLLOW_UP','CLOSED' | ForEach-Object { @{ name = $_ } }) },
        @{ type = 'text'; name = '主要问题' },
        @{ type = 'text'; name = '症状摘要JSON' },
        @{ type = 'text'; name = '已知病史快照' },
        @{ type = 'text'; name = '长期用药快照' },
        @{ type = 'text'; name = '医生反馈' },
        @{ type = 'select'; name = '反馈来源'; multiple = $false; options = $sourceOptions },
        @{ type = 'text'; name = '反馈来源原值'; description = '例如 doctor_reported_by_patient，保留精确来源语义' },
        @{ type = 'datetime'; name = '复查日期'; style = @{ format = 'yyyy-MM-dd' } }
    )
    '健康任务' = @(
        @{ type = 'text'; name = 'task_id' },
        @{ type = 'text'; name = 'member_id' },
        @{ type = 'text'; name = '任务类型' },
        @{ type = 'text'; name = '标题' },
        @{ type = 'text'; name = '描述' },
        @{ type = 'datetime'; name = '计划时间'; style = @{ format = 'yyyy-MM-dd HH:mm' } },
        @{ type = 'text'; name = '重复规则' },
        @{ type = 'select'; name = '来源'; multiple = $false; options = @('doctor','family','user','system' | ForEach-Object { @{ name = $_ } }) },
        @{ type = 'select'; name = '状态'; multiple = $false; options = @('pending','completed','cancelled' | ForEach-Object { @{ name = $_ } }) }
    )
    '检查资料索引' = @(
        @{ type = 'text'; name = 'document_id' },
        @{ type = 'text'; name = 'member_id' },
        @{ type = 'select'; name = '资料类型'; multiple = $false; options = @('physical_exam','lab_report','prescription','imaging','doctor_note','other' | ForEach-Object { @{ name = $_ } }) },
        @{ type = 'text'; name = '文件名' },
        @{ type = 'datetime'; name = '资料日期'; style = @{ format = 'yyyy-MM-dd' } },
        @{ type = 'text'; name = '摘要' },
        @{ type = 'select'; name = '来源'; multiple = $false; options = $sourceOptions },
        @{ type = 'checkbox'; name = '原文件仅本地保存' }
    )
}

$tables = @(Get-TableList)
$default = $tables | Where-Object table_name -eq 'Table' | Select-Object -First 1
if ($default -and -not ($tables.table_name -contains '家庭成员')) {
    & lark-cli base +table-update --base-token $BaseToken --table-id $default.table_id --name '家庭成员' --as user
    if ($LASTEXITCODE -ne 0) { throw '重命名默认表失败' }
}

foreach ($entry in $schemas.GetEnumerator()) {
    $tables = @(Get-TableList)
    $table = $tables | Where-Object table_name -eq $entry.Key | Select-Object -First 1
    if (-not $table) {
        New-BaseTable $entry.Key $entry.Value
        # 新建表已一次性携带全部字段；不要立刻回查补字段，避免飞书短暂一致性造成重复。
        continue
    }
    Add-MissingFields $table.table_id $entry.Value
}

Write-Host '飞书六张同步表已存在并完成字段补齐。'
