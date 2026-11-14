using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using MiloLib;
using MiloLib.Assets;
using MiloLib.Assets.Rnd;

if (args.Length == 4 && args[0] == "prepare-lanes")
{
    try
    {
        LaneAssets.Prepare(args[1], args[2], args[3]);
        return 0;
    }
    catch (Exception error)
    {
        Console.Error.WriteLine(error.ToString());
        return 1;
    }
}

if (args.Length != 3 || args[0] != "inspect")
{
    Console.Error.WriteLine("Usage: MiloTool inspect INPUT.milo_ps3 OUTPUT.json");
    Console.Error.WriteLine("       MiloTool prepare-lanes TRACK.milo_ps3 MESHES.milo_ps3 OUTPUT.json");
    return 2;
}

try
{
    var milo = new MiloFile(args[1]);
    var directories = new List<object>();
    var seen = new HashSet<DirectoryMeta>();
    object? TransformOf(MiloLib.Assets.Object obj)
    {
        var trans = obj switch
        {
            RndDir dir => dir.trans,
            RndMesh mesh => mesh.trans,
            RndGroup group => group.trans,
            RndTrans value => value,
            _ => null,
        };
        return trans == null ? null : new
        {
            parent = trans.parentObj.value,
            position = new[] { trans.localXfm.m41, trans.localXfm.m42, trans.localXfm.m43 },
            scale = new[] { trans.localXfm.m11, trans.localXfm.m22, trans.localXfm.m33 },
        };
    }
    void Walk(DirectoryMeta dir, string path)
    {
        if (!seen.Add(dir)) return;
        var entries = dir.entries.Select(entry => new
        {
            type = entry.type.value,
            name = entry.name.value,
            offset = entry.objBytesAbsolutePosition,
            size = entry.objBytes.Length,
            sha256 = Convert.ToHexStringLower(SHA256.HashData(entry.objBytes)),
            bytes = entry.type.value == "TrackWidget" ? entry.objBytes : null,
            widget = entry.obj is TrackWidget widget ? new
            {
                meshes = widget.meshes.Select(mesh => mesh.value).ToArray(),
                xOffset = typeof(TrackWidget).GetField("xOffset", BindingFlags.NonPublic | BindingFlags.Instance)!.GetValue(widget),
                widgetType = widget.widgetType.ToString(),
            } : null,
            transform = TransformOf(entry.obj),
            group = entry.obj is RndGroup group ? new
            {
                objects = group.objects.Select(value => value.value).ToArray(),
                drawOnly = group.drawOnly.value,
            } : null,
            material = entry.obj is RndMat mat ? new
            {
                color = new[] { mat.color.r, mat.color.g, mat.color.b, mat.color.a },
                blend = mat.blend.ToString(), diffuse = mat.diffuseTex.value,
            } : null,
            mesh = entry.obj is RndMesh mesh ? new
            {
                geometryOwner = mesh.geomOwner.value,
                vertices = mesh.vertices.vertices.Count,
                minX = mesh.vertices.vertices.Count == 0 ? 0 : mesh.vertices.vertices.Min(vertex => vertex.x),
                maxX = mesh.vertices.vertices.Count == 0 ? 0 : mesh.vertices.vertices.Max(vertex => vertex.x),
                minY = mesh.vertices.vertices.Count == 0 ? 0 : mesh.vertices.vertices.Min(vertex => vertex.y),
                maxY = mesh.vertices.vertices.Count == 0 ? 0 : mesh.vertices.vertices.Max(vertex => vertex.y),
                minZ = mesh.vertices.vertices.Count == 0 ? 0 : mesh.vertices.vertices.Min(vertex => vertex.z),
                maxZ = mesh.vertices.vertices.Count == 0 ? 0 : mesh.vertices.vertices.Max(vertex => vertex.z),
                material = mesh.mat.value,
            } : null,
            trigger = entry.obj is EventTrigger trigger ? new
            {
                animations = trigger.anims.Select(anim => anim.anim.value).ToArray(),
                launchers = trigger.partLaunchers.Select(launcher => launcher.value).ToArray(),
                shows = trigger.shows.Select(show => show.value).ToArray(),
            } : null,
            launcher = entry.obj is RndPartLauncher launcher ? new
            {
                transform = launcher.trans.value,
                particles = launcher.part.value,
            } : null,
            animation = entry.obj is RndTransAnim animation ? new
            {
                transform = animation.trans.value,
                positions = animation.transKeys.Count,
                scales = animation.scaleKeys.Count,
            } : null,
        }).ToArray();
        directories.Add(new
        {
            path, type = dir.type.value, name = dir.name.value,
            revision = dir.revision, dataOffset = dir.dirDataStartAbsolutePosition,
            transform = TransformOf(dir.directory),
            slots = dir.directory is TrackDir track ? track.slots.Select(slot => new[] {slot.m41, slot.m42, slot.m43}).ToArray() : null,
            entries,
        });
        if (dir.directory is ObjectDir objDir)
            foreach (var child in objDir.inlineSubDirs)
                Walk(child, path + "/" + child.name.value);
        foreach (var entry in dir.entries)
            if (entry.dir is { } child)
                Walk(child, path + "/" + entry.name.value);
    }
    Walk(milo.dirMeta, milo.dirMeta.name.value);
    var report = new { source = Path.GetFullPath(args[1]), endian = milo.endian.ToString(), directories };
    File.WriteAllText(args[2], JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
    Console.WriteLine($"Read {directories.Count} directories: {args[2]}");
    return 0;
}
catch (Exception error)
{
    Console.Error.WriteLine(error.ToString());
    return 1;
}
