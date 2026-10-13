-- Native adaptation of the Transitions.dev tabs-sliding interaction.
-- One short, on-demand movement; no background blur or continuous animation.
function Initialize()
    current = 0
    target = 0
    frame = 16
    last_checked = nil
    check_frame = 22
    last_open = nil
    panel_frame = 16
    panel_positions = {}
end

function Update()
    local measure = SKIN:GetMeasure('G_chk0b')
    local checked = measure and string.sub(measure:GetStringValue(),1,4) == 'Path'
    if last_checked ~= nil and checked and not last_checked and tonumber(SKIN:GetVariable('MotionEnabled')) == 1 then
        check_frame = 0
        SKIN:Bang('!CommandMeasure','MotionTimer','Stop 2')
        SKIN:Bang('!CommandMeasure','MotionTimer','Execute 2')
    end
    last_checked = checked
    local hidden = SKIN:GetMeasure('G_hid_ch')
    local opened = hidden and hidden:GetStringValue() == '0'
    if last_open ~= nil and opened and not last_open and tonumber(SKIN:GetVariable('MotionEnabled')) == 1 then
        StartPanel()
    elseif not opened and last_open then
        SKIN:Bang('!CommandMeasure','MotionTimer','Stop 3')
        RestorePanel()
    end
    last_open = opened
    return 0
end

-- Panel reveal: native 8 px travel, no blur, scale or changing widget dimensions.
function StartPanel()
    RestorePanel()
    panel_positions = {}
    local names = {'Ch_surface','Ch_title','Ch_close_surface','Ch_close_text','Ch_close',
        'Ch_tabs_track','Ch_pill','Ch_p0_t','Ch_p0','Ch_p1_t','Ch_p1','Ch_p2_t','Ch_p2',
        'Ch_line','Ch_cur','Ch_minmax','Ch_status'}
    local scale = tonumber(SKIN:GetVariable('Scale')) or 1
    for _,name in ipairs(names) do
        local meter = SKIN:GetMeter(name)
        if meter then
            local option = meter:GetOption('Y','0',false)
            local y = tonumber(meter:GetOption('Y','0')) or meter:GetY()
            table.insert(panel_positions,{name=name,option=option,y=y})
            SKIN:Bang('!SetOption',name,'Y',tostring(y+8*scale))
        end
    end
    panel_frame = 0
    SKIN:Bang('!CommandMeasure','MotionTimer','Stop 3')
    SKIN:Bang('!CommandMeasure','MotionTimer','Execute 3')
end

function RestorePanel()
    for _,row in ipairs(panel_positions or {}) do
        SKIN:Bang('!SetOption',row.name,'Y',row.option)
    end
    panel_positions = {}
    panel_frame = 16
    SKIN:Bang('!UpdateMeterGroup','ChartPanel')
end

function PanelAdvance()
    panel_frame = math.min(panel_frame+1,16)
    local scale = tonumber(SKIN:GetVariable('Scale')) or 1
    local offset = 8*scale*(1-panel_frame/16)^3
    for _,row in ipairs(panel_positions) do
        SKIN:Bang('!SetOption',row.name,'Y',tostring(row.y+offset))
    end
    if panel_frame == 16 then RestorePanel() end
    SKIN:Bang('!UpdateMeterGroup','ChartPanel')
    SKIN:Bang('!Redraw')
end

-- Inspired by Transitions.dev's free checkbox-check stroke reveal.
-- Runs only after the saved state reports completion; no optimistic false success.
function CheckAdvance()
    check_frame = math.min(check_frame+1,22)
    local scale = tonumber(SKIN:GetVariable('Scale')) or 1
    local progress = 1 - (1-check_frame/22)^3
    local a,b,c = {3.5,8.2},{6.5,11},{12,4.8}
    local first = math.sqrt((b[1]-a[1])^2+(b[2]-a[2])^2)
    local second = math.sqrt((c[1]-b[1])^2+(c[2]-b[2])^2)
    local distance = (first+second)*progress
    local path = tostring(a[1]*scale)..','..tostring(a[2]*scale)
    if distance <= first then
        local k = distance/first
        path = path..' | LineTo '..tostring((a[1]+(b[1]-a[1])*k)*scale)..','..tostring((a[2]+(b[2]-a[2])*k)*scale)
    else
        local k = (distance-first)/second
        path = path..' | LineTo '..tostring(b[1]*scale)..','..tostring(b[2]*scale)
        path = path..' | LineTo '..tostring((b[1]+(c[1]-b[1])*k)*scale)..','..tostring((b[2]+(c[2]-b[2])*k)*scale)
    end
    SKIN:Bang('!SetOption','Tk0_box','P',path)
    SKIN:Bang('!UpdateMeter','Tk0_box')
    SKIN:Bang('!Redraw')
end

function SelectPeriod(index)
    local scale = tonumber(SKIN:GetVariable('Scale')) or 1
    target = tonumber(index) * 64 * scale
    if frame == 16 then current = tonumber(SKIN:GetMeasure('G_ch_pillx'):GetStringValue()) or current end
    origin = current
    frame = 0
    local enabled = tonumber(SKIN:GetVariable('MotionEnabled')) or 0
    if enabled == 0 then
        current = target
        return
    end
    SKIN:Bang('!CommandMeasure', 'MotionTimer', 'Stop 1')
    SKIN:Bang('!CommandMeasure', 'MotionTimer', 'Execute 1')
end

function Advance()
    frame = math.min(frame + 1, 16)
    local progress = frame / 16
    local eased = 1 - (1 - progress)^3
    current = origin + (target - origin) * eased
    -- Offset the old selected geometry only during the transition.
    local scale = tonumber(SKIN:GetVariable('Scale')) or 1
    SKIN:Bang('!SetOption', 'Ch_pill', 'X', tostring(16 * scale + current))
    SKIN:Bang('!UpdateMeter', 'Ch_pill')
    SKIN:Bang('!Redraw')
    if frame == 16 then
        SKIN:Bang('!SetOption', 'Ch_pill', 'X', '(16*#Scale#+[G_ch_pillx])')
    end
end
