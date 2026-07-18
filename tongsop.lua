--// TONG SOP ULTRA SPLIT OPTIMIZER V3
--// KHUSUS SPLIT 4-8 ROBLOX
--// ANTI LAG + ANTI PANAS + ANTI FORCE CLOSE
--// AUTO HILANGKAN POPUP IKAN

repeat task.wait() until game:IsLoaded()

local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local Terrain = workspace:FindFirstChildOfClass("Terrain")
local RunService = game:GetService("RunService")

local LP = Players.LocalPlayer

-- =====================================
-- FPS LOCK
-- =====================================

pcall(function()
    if setfpscap then
        setfpscap(15)
    end
end)

-- =====================================
-- QUALITY SUPER LOW
-- =====================================

pcall(function()
    settings().Rendering.QualityLevel =
        Enum.QualityLevel.Level01
end)

-- =====================================
-- NOTIFIKASI
-- =====================================

pcall(function()

    game:GetService("StarterGui"):SetCore(
        "SendNotification",
        {
            Title = "TONG SOP ULTRA",
            Text = "SPLIT OPTIMIZER ACTIVE",
            Duration = 6
        }
    )

end)

-- =====================================
-- LIGHTING CLEAN
-- =====================================

pcall(function()

    Lighting.GlobalShadows = false
    Lighting.Brightness = 0
    Lighting.EnvironmentDiffuseScale = 0
    Lighting.EnvironmentSpecularScale = 0
    Lighting.FogEnd = 999999999

    for _,v in pairs(Lighting:GetChildren()) do

        if v:IsA("Sky")
        or v:IsA("Atmosphere")
        or v:IsA("BloomEffect")
        or v:IsA("BlurEffect")
        or v:IsA("ColorCorrectionEffect")
        or v:IsA("SunRaysEffect")
        or v:IsA("DepthOfFieldEffect")
        or v:IsA("PostEffect") then

            v:Destroy()

        end
    end
end)

-- =====================================
-- WATER OFF
-- =====================================

pcall(function()

    if Terrain then

        Terrain.WaterTransparency = 1
        Terrain.WaterReflectance = 0
        Terrain.WaterWaveSize = 0
        Terrain.WaterWaveSpeed = 0

    end
end)

-- =====================================
-- OPTIMIZE FUNCTION
-- =====================================

local function optimize(v)

    pcall(function()

        -- AUTO HANCURKAN SEMUA IKAN
        local lname = string.lower(v.Name)

        if string.find(lname,"fish")
        or string.find(lname,"ikan")
        or string.find(lname,"shark")
        or string.find(lname,"salmon")
        or string.find(lname,"tuna")
        or string.find(lname,"marlin") then

            pcall(function()

                if v:IsA("Model") then
                    v:Destroy()
                end

                if v:IsA("BasePart")
                or v:IsA("MeshPart") then
                    v:Destroy()
                end

                if v:IsA("Tool") then
                    v:Destroy()
                end

            end)
        end

        -- DESTROY TOTAL ROD / PANCING
        if v:IsA("Tool") then

            local n = string.lower(v.Name)

            if string.find(n,"rod")
            or string.find(n,"fishing")
            or string.find(n,"pancing") then

                v:Destroy()

            end
        end

        -- DESTROY ROD CONSTRAINT
        if v:IsA("RodConstraint")
        or v:IsA("RopeConstraint")
        or v:IsA("Beam") then

            v:Destroy()

        end

        -- HILANGKAN TOTAL CHARACTER
        if v:IsA("Model")
        and v:FindFirstChildOfClass("Humanoid") then

            for _,x in pairs(v:GetDescendants()) do

                pcall(function()

                    if x:IsA("BasePart") then
                        x.Transparency = 1
                        x.LocalTransparencyModifier = 1
                        x.CanCollide = false
                        x.CastShadow = false
                    end

                    if x:IsA("Decal")
                    or x:IsA("Texture") then
                        x:Destroy()
                    end

                    if x:IsA("Accessory") then
                        x:Destroy()
                    end

                end)

            end

        end

        -- EFFECT OFF
        if v:IsA("ParticleEmitter")
        or v:IsA("Trail")
        or v:IsA("Smoke")
        or v:IsA("Fire")
        or v:IsA("Sparkles") then

            v.Enabled = false

        end

        -- TEXTURE REMOVE
        if v:IsA("Texture")
        or v:IsA("Decal") then

            v:Destroy()

        end

        -- PART OPTIMIZE
        if v:IsA("BasePart") then

            v.Material = Enum.Material.SmoothPlastic
            v.CastShadow = false
            v.Reflectance = 0

            if not v:IsDescendantOf(LP.Character or workspace) then
                v.Transparency = 0.75
            end

        end

        -- MESH REMOVE TEXTURE
        if v:IsA("MeshPart") then

            v.TextureID = ""

        end

    end)
end

-- =====================================
-- CLEAN MAP BERTAHAP
-- =====================================

task.spawn(function()

    local objs = game:GetDescendants()

    for i,v in ipairs(objs) do

        optimize(v)

        if i % 200 == 0 then
            task.wait()
        end
    end

end)

-- =====================================
-- AUTO CLEAN OBJECT BARU
-- =====================================

game.DescendantAdded:Connect(function(v)

    task.spawn(function()
        optimize(v)
    end)

    -- AUTO HILANGKAN POPUP IKAN
    task.spawn(function()

        pcall(function()

            local n = string.lower(v.Name)

            if string.find(n,"fish")
            or string.find(n,"ikan")
            or string.find(n,"caught")
            or string.find(n,"reward")
            or string.find(n,"rare")
            or string.find(n,"epic")
            or string.find(n,"legendary")
            or string.find(n,"secret")
            or string.find(n,"mythic") then

                if v:IsA("ScreenGui")
                or v:IsA("BillboardGui") then

                    v.Enabled = false
                    v:Destroy()

                end

                if v:IsA("TextLabel")
                or v:IsA("ImageLabel")
                or v:IsA("Frame") then

                    v.Visible = false
                    v:Destroy()

                end

            end

        end)

    end)

end)

-- =====================================
-- LOOP OPTIMIZE
-- =====================================

task.spawn(function()

    while true do

        task.wait(3)

        pcall(function()

            local char = LP.Character

            if char then

                for _,v in pairs(char:GetDescendants()) do

                    if v:IsA("BasePart") then
                        v.Transparency = 1
                        v.LocalTransparencyModifier = 1
                        v.CastShadow = false
                    end

                end

            end

        end)

    end

end)

-- =====================================
-- MEMORY CLEAN
-- =====================================

task.spawn(function()

    while true do

        task.wait(10)

        pcall(function()
            collectgarbage("collect")
        end)

    end

end)

task.spawn(function()
    for _,v in ipairs(workspace:GetDescendants()) do
        pcall(function()

            if v:IsA("BasePart") then
                v.Material = Enum.Material.SmoothPlastic
                v.Color = Color3.fromRGB(110,110,110)
                v.CastShadow = false
                v.Reflectance = 0
            end

            if v:IsA("MeshPart") then
                v.TextureID = ""
                v.Color = Color3.fromRGB(110,110,110)
            end

            if v:IsA("Decal") or v:IsA("Texture") then
                v.Transparency = 1
            end

        end)
    end
end)

workspace.DescendantAdded:Connect(function(v)
    pcall(function()

        if v:IsA("BasePart") then
            v.Material = Enum.Material.SmoothPlastic
            v.Color = Color3.fromRGB(110,110,110)
            v.CastShadow = false
        end

        if v:IsA("MeshPart") then
            v.TextureID = ""
        end

        if v:IsA("Decal") or v:IsA("Texture") then
            v.Transparency = 1
        end

    end)
end)

task.spawn(function()
    while task.wait(1.5) do

        for _,plr in ipairs(game:GetService("Players"):GetPlayers()) do
            if plr.Character then
                pcall(function()

                    for _,v in ipairs(plr.Character:GetDescendants()) do
                        if v:IsA("BasePart") then
                            v.Transparency = 1
                            v.LocalTransparencyModifier = 1
                            v.CastShadow = false
                            v.CanCollide = false
                        end
                    end

                end)
            end
        end

    end
end)
