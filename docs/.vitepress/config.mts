import { defineConfig } from "vitepress";

const base = "/mrd"
// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "MRD",
  description: "MRD Documentation",
  head: [["link", { rel: "icon", href: `${base}/favicon.ico` }]],
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "Home", link: "/" },
      {
        text: "Reference",
        link: "/reference/model",
        activeMatch: "/reference/",
      },
    ],

    sidebar: {
      "/python/": [
        {
          text: "MRD Guide (Python)",
          collapsed: false,
          items: [
            { text: "Quick Start", link: "/python/quickstart" },
          ],
        },
        { text: "Reference", link: "/reference/model" },
      ],
      "/cpp/": [
        {
          text: "MRD Guide (C++)",
          collapsed: false,
          items: [
            { text: "Quick Start", link: "/cpp/quickstart" },
          ],
        },
        { text: "Reference", link: "/reference/model" },
      ],
      "/matlab/": [
        {
          text: "MRD Guide (MATLAB)",
          collapsed: false,
          items: [
            { text: "Quick Start", link: "/matlab/quickstart" },
          ],
        },
        { text: "Reference", link: "/reference/model" },
      ],
      "/reference/": [
        {
          text: "Reference",
          collapsed: false,
          items: [
            { text: "MRD Model", link: "/reference/model" },
            { text: "MRD Streaming Format", link: "/reference/format" },
            { text: "MRD Tools", link: "/reference/tools" },
          ],
        },
      ],
    },

    outline: {
      level: "deep",
    },

    socialLinks: [
      { icon: "github", link: "https://github.com/ismrmrd/mrd" },
    ],

    search: {
      provider: "local",
      options: {
        miniSearch: {
          options: {
            extractField(document, fieldName) {
              const fieldValue = document[fieldName];
              if (fieldName == "titles") {
                // Several documents have the same title in the Python and C++
                // documentation, which makes is hard to know which language a
                // search result is for. So we augment the "titles" field with
                // either C++ or Python if the document is under one of those paths.

                var documentId: string = document["id"];
                if (documentId.startsWith("/mrd/cpp")) {
                  // Include "C++"" in the search preview "path"
                  return ["C++"].concat(fieldValue);
                }

                if (documentId.startsWith("/mrd/python")) {
                  return ["Python"].concat(fieldValue);
                }

                if (documentId.startsWith("/mrd/matlab")) {
                  return ["MATLAB"].concat(fieldValue);
                }
              }

              return fieldValue;
            },
          },
        },
      },
    },
  },
  base: base,
  srcExclude: ["README.md"],
});
