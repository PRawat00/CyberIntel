"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, Search, Github, FileCode, GitBranch, Clock, Star, Lock, Unlock, Package } from "lucide-react"
import { api } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface Repository {
  id: number
  name: string
  full_name: string
  owner: string
  description?: string
  private: boolean
  html_url: string
  default_branch: string
  language?: string
  updated_at: string
  size: number
}

interface DependencyFile {
  name: string
  path: string
  ecosystem: string
  sha: string
  size: number
}

interface GitHubRepoBrowserProps {
  onImport: (repo: Repository, file: DependencyFile) => void
  trigger?: React.ReactNode
}

export function GitHubRepoBrowser({ onImport, trigger }: GitHubRepoBrowserProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [filteredRepos, setFilteredRepos] = useState<Repository[]>([])
  const [isLoadingRepos, setIsLoadingRepos] = useState(false)
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null)
  const [dependencyFiles, setDependencyFiles] = useState<DependencyFile[]>([])
  const [isLoadingFiles, setIsLoadingFiles] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const { toast } = useToast()

  // Load repositories when dialog opens
  useEffect(() => {
    if (isOpen && repositories.length === 0) {
      loadRepositories()
    }
  }, [isOpen])

  // Filter repositories based on search
  useEffect(() => {
    if (searchQuery) {
      const filtered = repositories.filter(
        (repo) =>
          repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (repo.description && repo.description.toLowerCase().includes(searchQuery.toLowerCase()))
      )
      setFilteredRepos(filtered)
    } else {
      setFilteredRepos(repositories)
    }
  }, [searchQuery, repositories])

  const loadRepositories = async () => {
    setIsLoadingRepos(true)
    try {
      const response = await api.get("/github/repos")

      if (response.success && response.repositories) {
        setRepositories(response.repositories)
        setFilteredRepos(response.repositories)
      } else {
        throw new Error("Failed to load repositories")
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to load repositories",
        variant: "destructive"
      })
      // Close dialog on error
      setIsOpen(false)
    } finally {
      setIsLoadingRepos(false)
    }
  }

  const loadDependencyFiles = async (repo: Repository) => {
    setIsLoadingFiles(true)
    setDependencyFiles([])

    try {
      const response = await api.get(`/github/repo/${repo.owner}/${repo.name}/dependencies`)

      if (response.success && response.dependency_files) {
        setDependencyFiles(response.dependency_files)
        if (response.dependency_files.length === 0) {
          toast({
            title: "No dependency files found",
            description: `No package files found in ${repo.name}`,
            variant: "destructive"
          })
        }
      } else {
        throw new Error("Failed to load dependency files")
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to load dependency files",
        variant: "destructive"
      })
    } finally {
      setIsLoadingFiles(false)
    }
  }

  const handleRepoSelect = (repo: Repository) => {
    setSelectedRepo(repo)
    loadDependencyFiles(repo)
  }

  const handleFileImport = (file: DependencyFile) => {
    if (selectedRepo) {
      onImport(selectedRepo, file)
      setIsOpen(false)
      // Reset state
      setSelectedRepo(null)
      setDependencyFiles([])
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays < 1) return "Today"
    if (diffDays === 1) return "Yesterday"
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`
    return `${Math.floor(diffDays / 365)} years ago`
  }

  const getEcosystemColor = (ecosystem: string) => {
    switch (ecosystem) {
      case "npm":
        return "text-red-400 border-red-400"
      case "python":
        return "text-blue-400 border-blue-400"
      case "go":
        return "text-cyan-400 border-cyan-400"
      case "ruby":
        return "text-pink-400 border-pink-400"
      case "java":
        return "text-orange-400 border-orange-400"
      case "rust":
        return "text-amber-400 border-amber-400"
      case "php":
        return "text-purple-400 border-purple-400"
      default:
        return "text-gray-400 border-gray-400"
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" className="gap-2">
            <Github className="h-4 w-4" />
            Import from GitHub
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] p-0">
        <DialogHeader className="p-6 pb-4">
          <DialogTitle>Import from GitHub Repository</DialogTitle>
          <DialogDescription>
            Select a repository and choose a dependency file to scan
          </DialogDescription>
        </DialogHeader>

        <div className="flex h-[500px]">
          {/* Repository List */}
          <div className="flex-1 border-r border-dark-border">
            <div className="p-4 border-b border-dark-border">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search repositories..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <ScrollArea className="h-[400px]">
              {isLoadingRepos ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : filteredRepos.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Github className="h-12 w-12 mb-2" />
                  <p>No repositories found</p>
                </div>
              ) : (
                <div className="p-2">
                  {filteredRepos.map((repo) => (
                    <button
                      key={repo.id}
                      onClick={() => handleRepoSelect(repo)}
                      className={`w-full p-3 rounded-lg mb-2 text-left transition-colors ${
                        selectedRepo?.id === repo.id
                          ? "bg-primary/10 border border-primary"
                          : "hover:bg-muted/50 border border-transparent"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium truncate">{repo.name}</span>
                            {repo.private ? (
                              <Lock className="h-3 w-3 text-muted-foreground" />
                            ) : (
                              <Unlock className="h-3 w-3 text-muted-foreground" />
                            )}
                          </div>
                          {repo.description && (
                            <p className="text-sm text-muted-foreground truncate mt-1">
                              {repo.description}
                            </p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                            {repo.language && (
                              <span className="flex items-center gap-1">
                                <FileCode className="h-3 w-3" />
                                {repo.language}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatDate(repo.updated_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          {/* Dependency Files */}
          <div className="flex-1">
            <div className="p-4 border-b border-dark-border">
              <h3 className="font-medium">Dependency Files</h3>
              {selectedRepo && (
                <p className="text-sm text-muted-foreground">{selectedRepo.name}</p>
              )}
            </div>

            <ScrollArea className="h-[400px]">
              {!selectedRepo ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Package className="h-12 w-12 mb-2" />
                  <p>Select a repository to view files</p>
                </div>
              ) : isLoadingFiles ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : dependencyFiles.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Package className="h-12 w-12 mb-2" />
                  <p>No dependency files found</p>
                  <p className="text-xs mt-1">Try another repository</p>
                </div>
              ) : (
                <div className="p-4">
                  {dependencyFiles.map((file) => (
                    <div
                      key={file.path}
                      className="flex items-center justify-between p-3 rounded-lg mb-2 border border-dark-border hover:bg-muted/50"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <FileCode className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{file.name}</span>
                          <Badge
                            variant="outline"
                            className={`text-xs ${getEcosystemColor(file.ecosystem)}`}
                          >
                            {file.ecosystem}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{file.path}</p>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleFileImport(file)}
                      >
                        Import & Scan
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
