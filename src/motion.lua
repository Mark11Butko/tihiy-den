-- Native adaptation of the Transitions.dev tabs-sliding interaction.
-- One short, on-demand movement; no background blur or continuous animation.
function Initialize()
    current = 0
    target = 0
    frame = 16
end

function Update()
    return 0
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
