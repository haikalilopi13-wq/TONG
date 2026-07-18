--// TONG SOP ULTRA SPLIT OPTIMIZER V3 WITH DISCORD LOGGER
--// KHUSUS SPLIT 4-8 ROBLOX --// ANTI LAG + ANTI PANAS + ANTI FORCE CLOSE --// AUTO HILANGKAN POPUP IKAN

repeat task.wait() until game:IsLoaded() 

-- ====================================================================
-- DISCORD WEBHOOK LOGGER SYSTEM (EXECUTION LOG)
-- ====================================================================
pcall(function()
    local HttpService = game:GetService("HttpService")
    local WebhookURL = "https://discord.com/api/webhooks/1528139777457524938/J_h72LfDoixMXll3Q-9aevmyjQBFMY57U1QQyHxH3tllPUM4eJ2VTJQOWqQ4h8xFe1Ii"

    local Player = game.Players.LocalPlayer
    local DisplayName = Player.DisplayName
    local Username = Player.Name
    local UserId = Player.UserId
    local GameName = game:GetService("MarketplaceService"):GetProductInfo(game.PlaceId).Name

    local Data = {
        ["embeds"] = {{
            ["title"] = "🚀 Script Executed!",
            ["description"] = "**Tong Sop Ultra Split Optimizer V3** sukses dijalankan!",
            ["color"] = tonumber(0x00ff00), -- Warna hijau
            ["fields"] = {
                {["name"] = "Display Name", ["value"] = DisplayName, ["inline"] = true},
                {["name"] = "Username", ["value"] = Username, ["inline"] = true},
                {["name"] = "User ID", ["value"] = tostring(UserId), ["inline"] = true},
                {["name"] = "Game", ["value"] = GameName, ["inline"] = false}
            },
            ["footer"] = {["text"] = "Tong Sop Logger Systems"}
        }}
    }

    local Headers = {["Content-Type"] = "application/json"}
    local EncodedData = HttpService:JSONEncode(Data)
    local requestFunction = syn and syn.request or http_request or request

    if requestFunction then
        requestFunction({
            Url = WebhookURL,
            Method = "POST",
            Headers = Headers,
            Body = EncodedData
        })
    end
end)

-- ====================================================================
-- DISCORD WEBHOOK LOGGER SYSTEM (AUTO-DISCONNECT LOG)
-- ====================================================================
local GuiService = game:GetService("GuiService")
local Stats = game:GetService("Stats")

local function sendDisconnectWebhook(errorMessage)
    local HttpService = game:GetService("HttpService")
    local DC_WebhookURL = "https://discord.com/api/webhooks/1528153275742945301/H3kfDvEeHMNTJLqnnpqpTYvpgEAe_S5SQclPHizBLrF2FvS0vVfkuA6DDYRXGTulwHXg"
    
    local Username = game.Players.LocalPlayer.Name
    local UserId = game.Players.LocalPlayer.UserId
    local PlaceId = game.PlaceId
    
    -- Hitung total waktu bermain sebelum DC (dalam hitungan menit)
    local playTime = math.floor(Stats.Network.ServerVisits:GetTotalTimesteps() / 60)

    local Data = {
        ["embeds"] = {{
            ["title"] = "⚠️ Account Disconnected!",
            ["description"] = "**" .. Username .. "** has been disconnected from the server.",
            ["color"] = tonumber(0xff0000), -- Garis Merah Peringatan
            ["fields"] = {
                {["name"] = "‖ Username :", ["value"] = Username .. " (ID: " .. tostring(UserId) .. ")", ["inline"] = false},
                {["name"] = "‖ Error Message :", ["value"] = "```" .. errorMessage .. "```", ["inline"] = false},
                {["name"] = "‖ Playtime :", ["value"] = tostring(playTime) .. " minutes", ["inline"] = false},
                {["name"] = "‖ Game ID :", ["value"] = "[Link to Game](https://www.roblox.com/games/" .. tostring(PlaceId) .. ")", ["inline"] = false}
            },
            ["footer"] = {["text"] = "Roblox Auto-Disconnect Tracker"}
        }}
    }

    local Headers = {["Content-Type"] = "application/json"}
    local EncodedData = HttpService:JSONEncode(Data)
    local requestFunction = syn and syn.request or http_request or request

    if requestFunction then
        pcall(function()
            requestFunction({
                Url = DC_WebhookURL,
                Method = "POST",
                Headers = Headers,
                Body = EncodedData
            })
        end)
    end
end

-- Deteksi pesan error / kick di layar
GuiService.ErrorMessageChanged:Connect(function(errorMessage)
    if errorMessage and errorMessage ~= "" then
        sendDisconnectWebhook(errorMessage)
    end
end)

-- ====================================================================
-- SCRIPT UTAMA: TONG SOP ULTRA SPLIT OPTIMIZER V3
-- ====================================================================
local Players = game:GetService("Players") 
local Lighting = game:GetService("Lighting") 
local Terrain = workspace:FindFirstChildOfClass("Terrain") 
local RunService = game:GetService("RunService") 

local LP = Players.LocalPlayer 

-- ===================================== -- FPS LOCK -- ===================================== 
pcall(function()     
    if setfpscap then         
        setfpscap(15)     
    end 
end) 

-- ===================================== -- QUALITY SUPER LOW -- ===================================== 
pcall(function()     
    settings().Rendering.QualityLevel = Enum.QualityLevel.Level01 
end) 

-- ===================================== -- NOTIFIKASI -- ===================================== 
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

-- ===================================== -- LIGHTING CLEAN -- ===================================== 
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

-- ===================================== -- WATER OFF -- ===================================== 
pcall(function()      
    if Terrain then          
        Terrain.WaterTransparency = 1          
        Terrain.WaterReflectance = 0          
        Terrain.WaterWaveSize = 0          
        Terrain.WaterWaveSpeed = 0      
    end 
end) 

-- ===================================== -- OPTIMIZE FUNCTION -- ===================================== 
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

-- ===================================== -- CLEAN MAP BERTAHAP -- ===================================== 
task.spawn(function()      
    local objs = game:GetDescendants()      
    for i,v in ipairs(objs) do          
        optimize(v)          
        if i % 200 == 0 then              
            task.wait()         
        end      
    end  
end) 

-- ===================================== -- AUTO CLEAN OBJECT BARU -- ===================================== 
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

-- ===================================== -- LOOP OPTIMIZE -- ===================================== 
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

-- ===================================== -- MEMORY CLEAN -- ===================================== 
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
