// upload files to the db
// query db (with vector search)

// and just return response.

import { v } from "convex/values";
import {
  query,
  action,
  internalMutation,
  internalQuery,
} from "./_generated/server";
import { internal } from "./_generated/api";

export type SearchResult = {
  _id: string;
  _score: number;
  description: string;
  content: string,
  response: Number[];
};



export const insert = action({
    args: { 
      name: v.string(), 
      company_name: v.string(), 
      description: v.string(), 
      content: v.string(), 
      embeddings: v.array(v.float64()) 
    },

    handler: async (ctx, args) => {
      const doc = {
        name: args.name,
        company_name: args.company_name,
        description: args.description,
        content: args.content,
        embedding: args.embeddings,
      };
      await ctx.runMutation(internal.docs.insertRow, doc);
    },
  });

export const insertRow = internalMutation({
    args: {
      name: v.string(),
      company_name: v.string(),
      description: v.string(),
      content: v.string(),
      embedding: v.array(v.float64()),
    },
    handler: async (ctx, args) => {
      await ctx.db.insert("documents", args);
    },
  });

export const get = query({
    handler: async ({ db }) => {
      return await db.query("documents").collect();
      
    },
  });

export const get_vector_id = query({
    args: { name: v.string(), company_name: v.string() },
    handler: async (ctx, args) => {
      return await ctx.db.query("documents").filter((q) => q.and(q.eq(q.field("name"), args.name), q.eq(q.field("company_name"), args.company_name))).collect();
      
    },
  });

export const fetchResults = internalQuery({
    args: {
      results: v.array(v.object({ _id: v.id("documents"), _score: v.float64() })),
    },
    handler: async (ctx, args) => {
      const out: SearchResult[] = [];
      for (const result of args.results) {
        const doc = await ctx.db.get(result._id);
        if (!doc) {
          continue;
        }
        out.push({
          _id: doc._id,
          _score: result._score,
          description: doc.description,
          content: doc.content,
          response: doc.embedding,
        });
      }
      return out;
    },
  });

export const doc_search = action({
    args: {
      query_embedding: v.array(v.float64()),
      company_name: v.string()
    },
    handler: async (ctx, args) => {
      
      const results = await ctx.vectorSearch("documents", "by_embeddings", {
        vector: args.query_embedding,
        limit: 16,
        filter: (q) => q.eq("company_name", args.company_name),
      });
      
      const doc_search_results: SearchResult[] = await ctx.runQuery(
        internal.docs.fetchResults, 
        { results }
      );
      return doc_search_results
    },
  });