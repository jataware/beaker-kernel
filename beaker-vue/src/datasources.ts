
const datasources = [
//   {
//   id: '1000',
//   name: 'NCI Genomic Data Commons',
//   initials: "GDC",
//   description: 'NCI\'s Genomic Data Commons (GDC) provides the cancer research community with a unified repository and cancer knowledge base that enables data sharing across cancer genomic studies in support of precision medicine. GDC enables access to data from various projects, genes, and mutations.',
//   // TODO -> icon
//   logo_url: "https://gdc.cancer.gov/sites/all/themes/gdc_bootstrap/logo.png",
//   "datasets": [
//     "Standardized data from cancer studies"
//   ],
//   "categories": [
//     "genomics"
//   ],
//   "tags": [
//     "human",
//     "genetics",
//     "cancer"
//   ],
//   "urls": {
//     "home_page": "https://gdc.cancer.gov",
//     "site_map": "",
//     "data_landing": "https://portal.gdc.cancer.gov",
//     "git_repository": "https://github.com/NCI-GDC",
//     "git_org": "https://github.com/NCIP",
//     "submission_portal": "https://portal.gdc.cancer.gov/submission",
//     "openapi_spec": "https://docs.gdc.cancer.gov/API/Users_Guide/Getting_Started"
//   },
//   "use_cases": [
//     "Standardized data access",
//     "Data analysis and visualization",
//     "Gene and variant level data analysis"
//   ],
//   "documentation": [
//     {
//       "name": "GDC Data Portal User\u2019s Guide",
//       "url": "https://docs.gdc.cancer.gov/Data_Portal/Users_Guide/getting_started"
//     },
//     {
//       "name": "GDC Data Transfer Tool User's Guide",
//       "url": "http://docs.gdc.cancer.gov/Data_Transfer_Tool/Users_Guide/Getting_Started"
//     },
//     {
//       "name": "GDC Application Programming Interface (API) User's Guide",
//       "url": "https://docs.gdc.cancer.gov/API/Users_Guide/Getting_Started"
//     }
//   ],
//   "collections": [
//     "case sets",
//     "projects"
//   ],
//   "data_categories": [
//     "Clinical",
//     "Biospecimen",
//     "Analytical Data"
//   ],
//   "data_types": [
//     "Genomic Data",
//     "Bioinformatic Pipelines"
//   ],
//   "file_formats": [
//     "json",
//     "tsv",
//     "bam",
//     "vcf",
//     "xlsx"
//   ],
//   "external_references": [
//     {
//       "name": "GDC Documentation",
//       "base_url": "https://docs.gdc.cancer.gov/"
//     },
//     {
//       "name": "GDC API",
//       "base_url": "https://docs.gdc.cancer.gov/API/Users_Guide/Getting_Started"
//     }
//   ],
//   "access_type": "mixed",
//   "capabilities": [
//     "workspaces",
//     "http_api",
//     "ui_case_search",
//     "ui_organ_search"
//   ],
//   "data_use_limitations": "Access to some datasets may be restricted due to patient confidentiality.",
//   "omics_methods": [
//     "Genomics",
//     "Bioinformatics"
//   ],
//   "contact": {
//     "email": "support@nci-gdc.datacommons.io",
//     "name": "GDC Help Desk"
//   },
// },
{
  id: '1001',
  name: 'Cancer Research Data Commons',
  "initials": "CBIIT",
  "description": "The CBIIT supports data sharing and science informatics related to cancer research. It offers guidance on data management and sharing policy through its Office of Data Sharing (ODS).",
  "logo_url": "https://datacommons.cancer.gov/themes/custom/crdc_foundation/images/logos/crdc_logo_color.svg",
  "datasets": [
    "NCI-funded research datasets",
    "International Cancer Proteogenome Consortium (ICPC) datasets"
  ],
  "categories": [
    "clinical",
    "genomics",
    "imaging"
  ],
  "tags": [
    "human",
    "genetics",
    "cancer"
  ],
  "urls": {
    "home_page": "https://datacommons.cancer.gov/",
    "data_landing": "https://datacommons.cancer.gov/explore",
    "submission_portal": "https://datacommons.cancer.gov/submit",
  },
  "use_cases": [
    "Data Management and Sharing Plan guidance",
    "Data submissions to CRDC data commons",
    "Access and analysis of data within CRDC",
    "Comparative analysis of cancer-related datasets",
    "Secure cloud workspace for bringing and analyzing own data"
  ],
  "documentation": [
    {
      "name": "Data Management and Sharing Policy Guidelines",
      "url": "https://datascience.cancer.gov/data-sharing/policies"
    },
    {
      "name": "NIH Scientific Data Sharing Repository Options",
      "url": "https://sharing.nih.gov/data-management-and-sharing-policy/sharing-scientific-data/repositories-for-sharing-scientific-data"
    },
    {
      "name": "NIH Allowable DMS Costs",
      "url": "https://sharing.nih.gov/data-management-and-sharing-policy/planning-and-budgeting-for-data-management-and-sharing/budgeting-for-data-management-sharing#allowable-costs"
    },
    {
      "name": "Submitting data to CRDC Data Commons",
      "url": "https://datacommons.cancer.gov/data"
    }
  ],
  "collections": [
    "case sets",
    "cohorts",
    "projects"
  ],
  "data_categories": [
    "genomic",
    "proteomic",
    "imaging",
    "canine",
    "Biological",
    "Biospecimen",
    "Clinical",
    "Data File",
    "Metadata",
    "Processed"
  ],
  "data_types": [
    "Proteogenomics",
    "Genomic analysis",
    "Molecular data",
    "Clinical data"
  ],
  "file_formats": [
    "json",
    "tsv",
    "bam",
    "tif",
    "png"
  ],
  "external_references": [],
  "access_type": "mixed",
  "capabilities": [
    "workspaces",
    "http_api",
    "ui_case_search",
    "ui_organ_search"
  ],
  "omics_methods": [
    "Genomics",
    "Proteomics",
    "Imaging"
  ],

  "data_use_limitations": "Data use limitations are subject to the policies outlined by NCI's Office of Data Sharing (ODS).",
  "contact": {
    "email": "NCIinfo@nih.gov",
    "name": "National Cancer Institute"
  },
},
// {
//   id: '1002',
//   "name": "NCI Proteomics Data Commons",
//   "initials": "PDC",
//   "description": "PDC is a fully open-access cancer proteomic dataportal that provides access to highly curated human cancer multi'omics data.",
//   "logo_url": "assets/css/images/PDC-NIH-Logo.png",
//   "datasets": [],
//   "categories": [
//     "clinical",
//     "genomics"
//   ],
//   "tags": [
//     "human",
//     "cancer",
//     "genetics"
//   ],
//   "urls": {
//     "home_page": "/",
//     "site_map": "",
//     "data_landing": "",
//     "git_repository": "",
//     "git_org": "",
//     "submission_portal": "/submitDataNavBar"
//   },
//   "use_cases": [],
//   "documentation": [
//     {
//       "name": "Data Dictionary",
//       "url": "/pdc/data-dictionary/data-dictionary-graph"
//     }
//   ],
//   "collections": [
//     "case sets",
//     "cohorts",
//     "projects"
//   ],
//   "data_types": [
//     "Case",
//     "Program",
//     "Project",
//     "Study",
//     "Gene",
//     "Aliquot",
//     "Analyte",
//     "Portion",
//     "Sample",
//     "Demographic",
//     "Diagnosis",
//     "Family History",
//     "Follow-Up",
//     "Exposure",
//     "Treatment",
//     "File",
//     "Aliquot Run Metadata",
//     "Protocol",
//     "Study Run Metadata",
//     "Workflow Metadata",
//     "Publication",
//     "Gene Abundance"
//   ],
//   "file_formats": [],
//   "external_references": [
//     {
//       "name": "NCI Thesaurus",
//       "base_url": "https://ncit.nci.nih.gov/ncitbrowser/pages/concept_details.jsf?dictionary=NCI%20Thesaurus&code="
//     }
//   ],
//   "access_type": "open",
//   "capabilities": [],
//   "data_use_limitations": "",
//   "omics_methods": [],
//   "contact": {
//     "email": "PDCHelpDesk@mail.nih.gov",
//     "name": "PDC Help Desk"
//   },
// },
{
  id: '1003',
  "name": "Clinical and Translational Data Commons",
  "initials": "CTDC",
  "description": "The Clinical and Translational Data Commons (CTDC) is being developed to accelerate scientific discoveries that make an impact on cancer outcomes to help people live longer, healthier lives. The CTDC supports cancer research by sharing NCI-funded clinical studies, with features including a Data Exploration dashboard, multiple data types including clinical (PDF, CSV) and molecular/sequencing data (bam/bai, vcf, tsv), data harmonization, data visualization and analysis on the cloud via Seven Bridges Cancer Genomics Cloud, developer resources including a Graphical user interface (GUI) and an Application Programming Interface (API), and a federated identity management system.",
  "logo_url": "https://datacommons.cancer.gov/themes/custom/crdc_foundation/images/logos/CRDC-logo-mobile.svg",
  "datasets": [
    "Cancer Moonshot Biobank (first release Fall 2023)"
  ],
  "categories": [
    "clinical",
    "genomics"
  ],
  "tags": [
    "human",
    "cancer"
  ],
  "urls": {
    "home_page": "https://datacommons.cancer.gov/",
    "data_landing": "/explore/data-commons"
  },
  "use_cases": [],
  "documentation": [
    {
      "name": "Seven Bridges Cancer Genomics Cloud",
      "url": "https://sevenbridges.com/cancer-genomics-cloud/"
    }
  ],
  "data_categories": [
    "Clinical data and reports",
    "Molecular findings and sequence annotation"
  ],
  "data_types": [
    "txt",
    "pdf",
    "vcf",
    "bam"
  ],
  "file_formats": [
    "txt",
    "pdf",
    "vcf",
    "bam",
    "bai",
    "tsv"
  ],

  "external_references": [
    {
      "name": "Biorepositories and Biospecimen Research Branch",
      "base_url": "https://biospecimens.cancer.gov"
    },
    {
      "name": "National Cancer Institute",
      "base_url": "https://www.cancer.gov"
    },
    {
      "name": "National Institutes of Health",
      "base_url": "https://www.nih.gov"
    },
    {
      "name": "U.S. Department of Health and Human Services",
      "base_url": "https://www.hhs.gov"
    },
    {
      "name": "USA.gov",
      "base_url": "https://www.usa.gov"
    }
  ],

  "access_type": "mixed",
  "capabilities": [
    "http_api",
    "ui_case_search"
  ],
  "data_use_limitations": "The data use limitations are not provided in the provided HTML snippet. This information would typically be detailed in a terms of service or use conditions document.",
  "omics_methods": [
    "genomics"
  ],
  "contact": {
    "email": "1-800-4-CANCER",
    "name": "Cancer Information Service"
  },

},
{
  id: '1004',
  name: 'Imaging Data Commons',
  "initials": "IDC",
  "description": "A guide providing information on how to interact with the Imaging Data Commons portal and utilize its various features. It includes guidance on downloading data, submitting data to IDC, and understanding the costs of using cloud resources. It also explains IDC's purpose, status, the data available, how to acknowledge IDC, and the differences between IDC and TCIA.",
  "logo_url": "https://storage.googleapis.com/idc-prod-web-static-files/static/img/NIH_IDC_title.svg",
  "datasets": [],
  "categories": [
    "imaging"
  ],
  "tags": [
    "human",
    "cancer"
  ],
  "urls": {
    "home_page": "https://portal.imaging.datacommons.cancer.gov/",
    "site_map": "",
    "data_landing": "",
    "git_repository": "https://github.com/ImagingDataCommons/IDC-Examples",
    "git_org": "",
    "submission_portal": "",
    "openapi_spec": "https://api.imaging.datacommons.cancer.gov/v1/swagger"
  },
  "use_cases": [
    "Explore metadata, visualize images and annotations, build cohorts from the data included in public TCIA collections",
    "Analyze TCIA public collections data on the cloud",
    "Use existing tools such as Google Colab, BigQuery, and DataStudio with the TCIA public collections data",
    "Perform complex queries against any of the DICOM attributes in the TCIA public collections",
    "Utilize other resources available in CRDC, such as CRDC Cloud Resources, for data analysis",
    "Quickly visualize specific images from TCIA public collections"
  ],
  "documentation": [
    {
      "name": "Downloading data",
      "url": "https://learn.canceridc.dev/data/downloading-data"
    },
    {
      "name": "Getting Started with IDC",
      "url": "https://learn.canceridc.dev/getting-started-with-idc"
    },
    {
      "name": "Google Colab",
      "url": "https://colab.research.google.com"
    },
    {
      "name": "Cancer Imaging Archive (TCIA)",
      "url": "https://www.cancerimagingarchive.net"
    },
    {
      "name": "Clinical Data Tutorial",
      "url": "https://github.com/ImagingDataCommons/IDC-Examples/blob/master/notebooks/clinical_data_intro.ipynb"
    },
    {
      "name": "Getting Started Tutorial Series",
      "url": "https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/getting_started"
    },
    {
      "name": "DataStudio Dashboard",
      "url": "https://datastudio.google.com/reporting/ab96379c-e134-414f-8996-188e678f1b70/page/KHtxB"
    }
  ],
  "collections": [
    "case sets",
    "cohorts"
  ],
  "data_categories": [
    "Cancer Imaging Archive (TCIA) collections",
    "HTAN and other pathology images"
  ],
  "data_types": [
    "Clinical data",
    "Imaging metadata"
  ],
  "file_formats": [
    "DICOM"
  ],
  "external_references": [
    {
      "name": "CRDC Cloud Resources",
      "base_url": "https://datacommons.cancer.gov"
    }
  ],
  "access_type": "open",
  "capabilities": [
    "ui_case_search"
  ],
  "data_use_limitations": "IDC only hosts public datasets. It does not support access limitations, such as data embargoes or sequestration.",
  "omics_methods": [],
  "contact": {
    "email": "support+submissions@canceridc.dev",
    "name": ""
  },
},

{
  id: '1005',
  "name": "Cancer Data Service",
  "initials": "CDS",
  "description": "The Cancer Data Service (CDS) is one of several data commons within the Cancer Research Data Commons (CRDC). CDS provides data storage and sharing capabilities for NCI-funded studies. It currently hosts a variety of data types from NCI projects such as the Human Tumor Atlas Network (HTAN), Division of Cancer Control and Population Sciences (DCCPS), Childhood Cancer Data Initiative (CCDI), and data from independent research projects. The CDS is home to both open and controlled access data, but the CDS Portal is accessible for users to search and browse with no login. Users can see if the CDS has data of interest before requesting access.",
  "logo_url": "https://raw.githubusercontent.com/CBIIT/datacommons-assets/main/cds/logo/cds-logo.svg",
  "datasets": [
    "Childhood Cancer Data Initiative (CCDI): Genomic Analysis in Pediatric Malignancies - phs002430.v1.p1",
    "DCCPS CIDR: The Role of Rare Coding Variation in Prostate Cancer in Men of African Ancestry - RESPOND Project 2 \u2013 phs002637.v1.p1",
    "CCDI: MCI - Molecular Characterization Initiative \u2013 phs002790.v5.p1",
    "TCGA WGS Variants Across 18 Cancer Types - phs003155.v1.p1"
  ],
  "categories": [
    "genomics",
    "imaging"
  ],
  "tags": [
    "human",
    "genetics",
    "cancer"
  ],
  "urls": {
    "home_page": "https://dataservice.datacommons.cancer.gov/#/home",
    "data_landing": "https://dataservice.datacommons.cancer.gov/#/submit",
    "submission_portal": "https://dataservice.datacommons.cancer.gov/#/submit"
  },
  "use_cases": [
    "Data storage and sharing for NCI-funded studies",
    "Search and browse data of interest before requesting access"
  ],
  "documentation": [
    {
      "name": "CDS User Guide",
      "url": "https://docs.cancergenomicscloud.org/v1.0/page/cds-data"
    },
    {
      "name": "CDS portal's Data Submission page",
      "url": "https://dataservice.datacommons.cancer.gov/#/submit"
    },
    {
      "name": "CDS Access and Analysis page",
      "url": "https://dataservice.datacommons.cancer.gov/#/analysis"
    }
  ],
  "collections": [
    "cohorts"
  ],
  "data_categories": [
    "open access",
    "controlled access"
  ],
  "file_formats": [
    "not specified"
  ],
  "external_references": [
    {
      "name": "dbGaP",
      "base_url": "https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin"
    }
  ],
  "access_type": "mixed",
  "capabilities": [
    "http_api",
    "ui_case_search"
  ],
  "data_use_limitations": "The CDS is home to both open and controlled access data. Open-access data are publicly accessible; no approval is required. For controlled-access data, users must request access and obtain approval.",
  "omics_methods": [
    "genomic",
    "imaging"
  ],
  "contact": {
    "email": "CDSHelpDesk@mail.nih.gov"
  },
}];

export default datasources;
