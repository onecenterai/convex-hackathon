import { v } from "convex/values";
import { defineSchema, defineTable } from "convex/server";

export default defineSchema({
    documents: defineTable({
        name: v.string(),
        company_name: v.string(),
        description: v.string(),
        content: v.string(),
        embedding: v.array((v.float64())),
    }).vectorIndex("by_embeddings", {
        vectorField: "embedding",
        dimensions: 1536,
        filterFields: ["name", "company_name"],
    })
});