using System.Security.Cryptography;
using System.Text.Json;
using MiloLib;
using MiloLib.Assets;
using MiloLib.Assets.Rnd;
using MiloLib.Utils;

static class LaneAssets
{
    static readonly byte[] End = [0xad, 0xde, 0xad, 0xde];
    static readonly string[] Parts = ["snare", "high_tom", "middle_tom", "floor_tom", "hihat", "ride", "crash"];
    const float WidthScale = 0.5f;

    static DirectoryMeta.Entry Clone(DirectoryMeta parent, DirectoryMeta.Entry source, string name)
    {
        var clone = new DirectoryMeta.Entry(source.type, name, null!) { objBytes = source.objBytes.ToArray() };
        using var reader = new EndianReader(source.objBytes.Concat(End).ToArray(), Endian.BigEndian);
        parent.ReadEntry(reader, clone);
        if (reader.BaseStream.Position != reader.BaseStream.Length)
            throw new InvalidDataException($"Object did not consume its complete payload: {source.name}");
        return clone;
    }

    static byte[] Serialize(DirectoryMeta parent, DirectoryMeta.Entry entry)
    {
        using var stream = new MemoryStream();
        using var writer = new EndianWriter(stream, Endian.BigEndian);
        parent.WriteEntry(writer, entry);
        var bytes = stream.ToArray();
        if (!bytes.AsSpan(bytes.Length - 4).SequenceEqual(End))
            throw new InvalidDataException($"Serialized object lacks its end marker: {entry.name}");
        return bytes[..^4];
    }

    public static void Prepare(string trackPath, string meshPath, string output)
    {
        var track = new MiloFile(trackPath);
        var geometry = new MiloFile(meshPath);
        var targets = new List<object>();
        var seen = new HashSet<DirectoryMeta>();
        void Walk(DirectoryMeta dir, string path)
        {
            if (!seen.Add(dir)) return;
            if (dir.type.value == "GemTrackDir")
                targets.Add(PrepareDirectory(track, dir, geometry.dirMeta, path));
            if (dir.directory is ObjectDir obj)
                foreach (var child in obj.inlineSubDirs) Walk(child, path + "/" + child.name.value);
            foreach (var entry in dir.entries)
                if (entry.dir is { } child) Walk(child, path + "/" + entry.name.value);
        }
        Walk(track.dirMeta, track.dirMeta.name.value);
        if (targets.Count == 0) throw new InvalidDataException("No GemTrackDir directories found");
        var manifest = new
        {
            sourceSha256 = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(trackPath))),
            widthScale = WidthScale, directories = targets,
        };
        File.WriteAllText(output, JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true }));
        Console.WriteLine($"Prepared lane objects for {targets.Count} track directories: {output}");
    }

    static long DirectoryEnd(DirectoryMeta dir)
    {
        var end = dir.dirDataStartAbsolutePosition + dir.DirObjBytes.Length;
        foreach (var entry in dir.entries)
        {
            end = Math.Max(end, entry.objBytesAbsolutePosition + entry.objBytes.Length + End.Length);
            if (entry.dir is { } child) end = Math.Max(end, DirectoryEnd(child));
        }
        if (dir.directory is ObjectDir obj)
            foreach (var child in obj.inlineSubDirs) end = Math.Max(end, DirectoryEnd(child));
        return end;
    }

    static object PrepareDirectory(MiloFile track, DirectoryMeta root, DirectoryMeta geometry, string path)
    {
        if (root.revision != 28 || root.type.value != "GemTrackDir")
            throw new InvalidDataException("Expected the revision-28 PS3 GemTrackDir asset");
        var entries = root.entries.ToDictionary(entry => entry.name.value);
        var geometries = geometry.entries.ToDictionary(entry => entry.name.value);
        var sourceWidgets = root.entries.Where(entry => entry.obj is TrackWidget &&
            (entry.name.value.StartsWith("drum_") || entry.name.value.StartsWith("cymbal_gem_") ||
             entry.name.value.StartsWith("dynamic_crash_"))).ToArray();
        if (sourceWidgets.Length == 0) throw new InvalidDataException("No drum widgets found");
        var newEntries = new List<object>();
        var narrowedMeshes = new HashSet<string>();
        void Add(DirectoryMeta.Entry entry, string source)
        {
            newEntries.Add(new { type = entry.type.value, name = entry.name.value, source,
                bytes = Serialize(root, entry) });
        }
        foreach (var source in sourceWidgets)
        {
            var widget = (TrackWidget)source.obj;
            foreach (var symbol in widget.meshes)
            {
                var meshName = symbol.value;
                if (!narrowedMeshes.Add(meshName)) continue;
                var name = "dx_lane_" + meshName;
                var clone = Clone(root, entries[meshName], name);
                var mesh = (RndMesh)clone.obj;
                if (mesh.vertices.vertices.Count == 0)
                {
                    var owner = mesh.geomOwner.value;
                    if (!geometries.TryGetValue(owner, out var ownerEntry))
                        throw new InvalidDataException($"Cannot resolve geometry owner {owner} for {meshName}");
                    var ownerClone = (RndMesh)Clone(geometry, ownerEntry, name).obj;
                    mesh.vertices = ownerClone.vertices;
                    mesh.faces = ownerClone.faces;
                    mesh.groupSizes = ownerClone.groupSizes;
                }
                if (mesh.vertices.vertices.Count == 0)
                    throw new InvalidDataException($"Cannot narrow an empty mesh: {meshName}");
                for (var i = 0; i < mesh.vertices.vertices.Count; i++)
                {
                    var vertex = mesh.vertices.vertices[i];
                    vertex.x *= WidthScale;
                    var nx = vertex.nx / WidthScale;
                    var length = MathF.Sqrt(nx * nx + vertex.ny * vertex.ny + vertex.nz * vertex.nz);
                    if (length > 0)
                    {
                        vertex.nx = nx / length;
                        vertex.ny /= length;
                        vertex.nz /= length;
                        vertex.hasRawCompressedVertexData = false;
                    }
                    mesh.vertices.vertices[i] = vertex;
                }
                mesh.geomOwner = name;
                Add(clone, meshName);
            }
        }
        foreach (var part in Parts)
        {
            foreach (var source in sourceWidgets)
            {
                var clone = Clone(root, source, $"dx_lane_{part}_{source.name.value}");
                var widget = (TrackWidget)clone.obj;
                widget.meshes = widget.meshes.Select(mesh => (Symbol)("dx_lane_" + mesh.value)).ToList();
                Add(clone, source.name.value);
            }
            foreach (var cymbal in new[] { false, true })
            {
                var color = part switch
                {
                    "snare" => "red",
                    "high_tom" or "hihat" => "yellow",
                    "middle_tom" or "ride" => "blue",
                    _ => "green",
                };
                var sourceName = cymbal ? $"cymbal_gem_{color}.wid" : $"drum_{color}.wid";
                var suffix = cymbal ? "cymbal_gem_miss.wid" : "drum_miss.wid";
                var clone = Clone(root, entries[sourceName], $"dx_lane_{part}_{suffix}");
                var widget = (TrackWidget)clone.obj;
                widget.meshes = widget.meshes.Select(mesh => (Symbol)("dx_lane_" + mesh.value)).ToList();
                Add(clone, sourceName);
            }
        }
        var streamBase = track.compressionType == MiloFile.Type.Uncompressed ? track.StartOffset : 0;
        return new
        {
            path,
            headerOffset = root.stringTableAbsolutePosition - streamBase - 12 -
                System.Text.Encoding.Latin1.GetByteCount(root.type.value) - System.Text.Encoding.Latin1.GetByteCount(root.name.value),
            dataOffset = root.dirDataStartAbsolutePosition - streamBase,
            endOffset = DirectoryEnd(root) - streamBase,
            originalEntries = root.entries.Count,
            preserved = root.entries.Select(entry => new { name = entry.name.value,
                sha256 = Convert.ToHexStringLower(SHA256.HashData(entry.objBytes)) }).ToArray(),
            entries = newEntries,
        };
    }
}
